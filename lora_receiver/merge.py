import os
from PIL import Image, ImageFile
import time
import sys
sys.path.append('.')
sys.path.append('..')

import config
import uploader
import __main__

CROP_SIZE = config.CROP_SIZE
WIDTH = config.LORA_IMG_WIDTH
HEIGHT = config.LORA_IMG_HEIGHT

ImageFile.LOAD_TRUNCATED_IMAGES = True

RX_BUFFER = './lora_receiver/rx_buffer/'
MISS_IMG = './lora_receiver/miss_img/'

def is_update(path):
    f = open(f'{path}/update.txt', 'r')
    update = f.read()
    f.close()
    f = open(f'{path}/.merge.update.txt', 'w')
    f.write('0')
    f.close()
    os.rename(
        f'{path}/.merge.update.txt',
        f'{path}/update.txt'
    )
    return update

def segment_merge(path):
    segment_list = os.listdir(path)
    segment_list = sorted([int(i) for i in segment_list])
    final = b''
    for s in segment_list:
        f = open(f'{path}/{s}', 'rb')
        final += f.read()
        f.close()
    return final

count = 0
img_list = os.listdir(RX_BUFFER)
fail_list = []
for img in img_list:
    if not os.path.isdir(RX_BUFFER + img) or img == 'sp' or img == 'uploaded':
        continue
    print(img, time.ctime())
    if is_update(RX_BUFFER + img) == '0':
        print('Skip')
        continue
    img_parts = os.listdir(RX_BUFFER + img)
    result_img = Image.new(mode = "RGB", size = (WIDTH, HEIGHT))
    for part in sorted(img_parts):
        if not os.path.isdir(f'{RX_BUFFER}{img}/{part}'):
            continue
            # part = part.split('.')[0]
        else:   #for easy debug
            try:
                f = open(f'{RX_BUFFER}{img}/{part}.jpg', 'wb')
            except:
                print('Error opening main image')
                continue
            f.write(segment_merge(f'{RX_BUFFER}{img}/{part}'))
            f.close()
        x,y = part.split('_')
        #add
        part_parts = sorted(int(i) for i in os.listdir(RX_BUFFER + img +'/'+ part))
        #print(part_parts,x,y)
        #print(f'{len(part_parts)} != {int(part_parts[-1]) + 1}')
        if len(part_parts) != int(part_parts[-1]) + 1:
            fail_list.append([int(x),int(y)])
            print(f'{part} fail')
        else:
            try:
                result_img.paste(Image.open(f'{RX_BUFFER}{img}/{part}.jpg'), (CROP_SIZE*int(x), CROP_SIZE*int(y)))
                print(f'{part} ok')
            except:
                print(f'{part} fail')
                
                fail_list.append([int(x),int(y)])
    fail_list.insert(0,img)
    print(f'send again')
    print(fail_list[1:])
    fimg = int(img)
    header = b''
    header = bytes([fimg//256, fimg%256])
    for i in fail_list[1:]:
        x,y = i
        header += bytes([x,y])
    print(header)
 
    if len(fail_list) > 1:
        if not os.path.isdir(f'{MISS_IMG}{img}'):
            os.mkdir(f'{MISS_IMG}{img}')
        f = open(f'{MISS_IMG}{img}/missing.txt', 'wb')
        f.write(header)
        f.close
    fail_list=[]
    #loras[0].lora_tx(header,4,0)
    
    result_img.save(RX_BUFFER + img + '.jpg')
    
    try:
        print(uploader.upload_image(RX_BUFFER + img + '.jpg'))
        uploader.upload_tx_status()
        uploader.upload_rx_status()
    except KeyboardInterrupt:
        print('User exit (Ctrl + C)')
    except:
        print('Post error')
    
