import shutil
import glob
import os


source_dir = "./tie_sim_data/insert-little-end-tie/normal/000/"
target_dir = "./tie_sim_data/knot-tie/normal/000/"
source_file_list = os.listdir(source_dir)
source_file_list.sort()
for file in source_file_list:
    new_name = "%04d.png" % (int(file[:-4]) + 871)
    print(new_name)
    shutil.copyfile(f"{source_dir}/{file}", f"{target_dir}/{new_name}")