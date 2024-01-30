import os
import time

os.system('python -u ./camera_controller/wifi_turnon.py')
time.sleep(5)
os.system('python -u ./camera_controller/wifi_connect.py')
time.sleep(10)
os.system('python -u ./camera_controller/image_download.py')
time.sleep(5)
os.system('python -u ./camera_controller/wifi_disconnect.py')
time.sleep(5)
os.system('python -u ./camera_controller/wifi_turnoff.py')