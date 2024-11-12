import os
import shutil


task_dir = "../tie_real_data"
dataset_dir = "../datasets/metaworld/metaworld_dataset/"
task_list = os.listdir(task_dir)
for task in task_list:
    if task == "pull-little-end-tie-down":
        # os.system(f"python train_mw.py --mode inference -c 8 -p ../examples/{task}.png -t {task} --destination_task {task}")
        continue
    else:
        os.system(f"python train_mw.py --mode inference -c 5 -p ../examples/{task}.png -t {task} --destination_task {task}")
