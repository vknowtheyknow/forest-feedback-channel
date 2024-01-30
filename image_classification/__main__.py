import os
from PIL import Image
import classification
import time

source_dir = './image_buffer/imported/'
file_list = sorted(os.listdir(source_dir))
total_img = len(file_list)
t = time.time()
for i in range(total_img):
    file_name = file_list[i]
    print(f'{i+1}/{total_img}| {file_name}:', end=' ')
    if classification.interested(source_dir+file_name):
        os.rename(source_dir + file_name, f'./image_buffer/interested/queue/{file_name}')
    else:
        os.rename(source_dir + file_name, f'./image_buffer/disinterested/{file_name}')
    print(f' : {time.time() - t:.2f} sec')
    t = time.time()
    os.system('python -u ./image_classification/crop.py')
