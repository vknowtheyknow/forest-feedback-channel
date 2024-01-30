import os
import math
from PIL import Image
import sys
sys.path.append('.')
sys.path.append('..')
import config

CROP_SIZE = config.CROP_SIZE
QUALITY = config.QUALITY
width = config.LORA_IMG_WIDTH
height = config.LORA_IMG_HEIGHT

CONTINUE = True

def img_crop(filename):
    origin_img = Image.open(f'{source_dir}{filename}').convert('L')
    print(1)
    global width, height
    try:
        origin_img = origin_img.resize((width, height), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Error resizing image: {e}")
    print(2)
    width, height = origin_img.size
    width, height = math.ceil(width/CROP_SIZE), math.ceil(height/CROP_SIZE)
    print(3)
    filename = filename.split('.')[0].split('_')[1]
    print(4)
    os.mkdir(f'./image_buffer/segmented/{filename}/')
    print('create file segment')
    for x in range(width):
        for y in range(height):
            left = x * CROP_SIZE
            top = y * CROP_SIZE
            right = (x+1)*CROP_SIZE
            bottom = (y+1)*CROP_SIZE
            origin_img.crop(
                    (left, top, right, bottom)
                ).save(f'./image_buffer/segmented/{filename}/{x}_{y}.jpg', 
                    optimize=True, 
                    quality=QUALITY)
    origin_img.save(f'./image_buffer/segmented/{filename}.jpg', 
                optimize=True, 
                quality=QUALITY)

source_dir = './image_buffer/interested/queue/'
file_list = os.listdir(source_dir)
for file_name in file_list:
    print(file_name)
    try:
        img_crop(file_name)
        os.rename(source_dir + file_name, f'./image_buffer/interested/{file_name}')
    except:
        print('CROP ERROR')
    print('CROP Done')
