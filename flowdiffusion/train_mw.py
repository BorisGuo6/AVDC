from goal_diffusion import GoalGaussianDiffusion, Trainer
from unet import UnetMW as Unet
from transformers import CLIPTextModel, CLIPTokenizer
from datasets import SequentialDatasetv2
from torch.utils.data import Subset
import argparse
import cv2
import os


def main(args):
    valid_n = 1
    sample_per_seq = 24
    target_size = (128, 128)

    if args.mode == 'inference':
        train_set = valid_set = [None] # dummy
    else:
        train_set = SequentialDatasetv2(
            sample_per_seq=sample_per_seq, 
            path="../datasets/metaworld", 
            target_size=target_size,
            randomcrop=True
        )
        valid_inds = [i for i in range(0, len(train_set), len(train_set)//valid_n)][:valid_n]
        valid_set = Subset(train_set, valid_inds)

    unet = Unet()

    pretrained_model = "openai/clip-vit-base-patch32"
    tokenizer = CLIPTokenizer.from_pretrained(pretrained_model)
    text_encoder = CLIPTextModel.from_pretrained(pretrained_model)
    text_encoder.requires_grad_(False)
    text_encoder.eval()

    diffusion = GoalGaussianDiffusion(
        channels=3*(sample_per_seq-1),
        model=unet,
        image_size=target_size,
        timesteps=100,
        sampling_timesteps=args.sample_steps,
        loss_type='l2',
        objective='pred_v',
        beta_schedule = 'cosine',
        min_snr_loss_weight = True,
    )

    trainer = Trainer(
        diffusion_model=diffusion,
        tokenizer=tokenizer, 
        text_encoder=text_encoder,
        train_set=train_set,
        valid_set=valid_set,
        train_lr=0.625e-5,
        train_num_steps =100000,
        save_and_sample_every =25000,
        ema_update_every = 10,
        ema_decay = 0.999,
        train_batch_size =1,
        valid_batch_size =2,
        gradient_accumulate_every = 1,
        num_samples=valid_n, 
        results_folder=f'../results/mw/{args.destination_task}',
        fp16 =True,
        amp=True,
    )

    if args.checkpoint_num is not None:
        trainer.load(args.checkpoint_num)
    
    if args.mode == 'train':
        trainer.train()
    else:
        from PIL import Image
        from torchvision import transforms
        import imageio
        import torch
        from os.path import splitext
        text = args.text
        guidance_weight = args.guidance_weight
        image = Image.open(args.inference_path)
        batch_size = 1
        ### 231130 fixed center crop issue 
        transform = transforms.Compose([
            # transforms.Resize((240, 320)),
            transforms.CenterCrop(target_size),
            transforms.ToTensor(),
        ])
        image = transform(image)
        output = trainer.sample(image.unsqueeze(0), [text], batch_size, guidance_weight).cpu()
        output = output[0].reshape(-1, 3, *target_size)
        output = torch.cat([image.unsqueeze(0), output], dim=0)
        root, ext = splitext(args.inference_path)
        output_gif = root + '_out.gif'
        output = (output.cpu().numpy().transpose(0, 2, 3, 1).clip(0, 1) * 255).astype('uint8')
        print(output.shape)
        if not os.path.exists(f"../examples/{root}-seq/"):
            os.makedirs(f"../examples/{root}-seq/")
        for f in range(output.shape[0]):
            frame = cv2.cvtColor(output[f], cv2.COLOR_RGB2BGR)
            cv2.imwrite(f"../examples/{root}-seq/{f}.png", frame)
        imageio.mimsave(output_gif, output, duration=200, loop=1000)
        print(f'Generated {output_gif}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', type=str, default='train', choices=['train', 'inference']) # set to 'inference' to generate samples
    parser.add_argument('-c', '--checkpoint_num', type=int, default=None) # set to checkpoint number to resume training or generate samples
    parser.add_argument('-p', '--inference_path', type=str, default=None) # set to path to generate samples
    parser.add_argument('-t', '--text', type=str, default=None) # set to text to generate samples
    parser.add_argument('-n', '--sample_steps', type=int, default=100) # set to number of steps to sample
    parser.add_argument('-g', '--guidance_weight', type=int, default=0) # set to positive to use guidance
    parser.add_argument('-d', '--destination_task', type=str, default='pull-little-end-tie-up', choices=['pull-little-end-tie-down',
                                                                                                         'pull-large-end-tie-up',
                                                                                                         'flip-ring-from-right-to-left',
                                                                                                         'rotate-ring-up',
                                                                                                         'pull-two-rings-together',
                                                                                                         'insert-little-end-tie',
                                                                                                         'pull-little-end-up-and-pull-large-end-down',
                                                                                                         'knot-simulation-tie',
                                                                                                         'knot-real-tie']) # set to positive to use guidance
    args = parser.parse_args()
    if args.mode == 'inference':
        assert args.checkpoint_num is not None
        assert args.inference_path is not None
        assert args.text is not None
        assert args.sample_steps <= 100
    main(args)