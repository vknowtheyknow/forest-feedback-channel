import requests
import sys
import time
sys.path.append('.')
sys.path.append('..')
import config

CAMERA_IP = config.CAM_IP

def get_local_list():
	global file_index
	f = open('./image_buffer/camera_files_map', 'r')
	local_list = f.read().split('\n')
	f.close()
	return local_list

def save_local_list(local_list):
    f = open('./image_buffer/camera_files_map', 'w')
    for path in local_list:
        f.write(path + '\n')
    f.close()
    print('Local images list updated')

def save_camera_status(ind):
    if ind == '':
        ind = '0'
    f = open('./image_buffer/camera_status', 'w')
    f.write(str(ind) + '\n')
    f.write(str(round(time.time())) + '\n')
    f.close()

try:
# if True:
    raw_img_list = requests.get(f'http://{CAMERA_IP}/DCIM/PHOTO', timeout=10).text
    raw_img_list = raw_img_list.split('\n')
    img_list = []
    # print(raw_img_list)
    for line in raw_img_list:
        if line[:29] == '<tr><td><a href="/DCIM/PHOTO/':
            img_list.append(line.split('"')[1])
    camera_list = set(img_list)
    print("Got camera\'s images list")

    local_list = set(get_local_list())
    if len(camera_list)*2 < len(local_list):
        local_list = set([])
    for img_path in sorted(list(camera_list - local_list)):
        img_name = img_path.split('/')[-1].replace('IM', 'IMG')
        print(f'Downloading', img_name)
        try:
            res = requests.get(f'http://{CAMERA_IP}{img_path}', timeout=10)
        except requests.exceptions.Timeout:
            print('Error downloading timeout')
        f = open(f'./image_buffer/imported/{img_name}', 'wb')
        f.write(res.content)
        f.close()
    local_list = sorted(list(local_list.union(camera_list)))
    save_local_list(local_list)
    save_camera_status(local_list[-1][15:20]) #'/DCIM/PHOTO/IM_00010.JPG' -> '00010'
except requests.exceptions.Timeout:
    print('Error downloading timeout')
except:
    print('Error downloading image')