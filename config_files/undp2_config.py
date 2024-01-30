# for UNDP_2 device
print('UNDP_2')

# import sys
# sys.path.append('.')  #when run from ~/lora-multi-ch
# sys.path.append('..') #when run from module's dir
# import config

# rm config.py; ln -s ./config_files/undp2_config.py config.py

# Camera
CAM_MAC_ADDRESS = '62:00:a1:15:04:84'
CAM_SSID = 'Campark-T86-4a1732bb0144'
CAM_PSK = '12345678'
CAM_IP = '192.168.8.120'

# Image
CROP_SIZE = 64
QUALITY = 20
LORA_IMG_WIDTH = 640
LORA_IMG_HEIGHT = 360

# LoRa
PACKET_SIZE = 40
SF = 12
CH0_FREQ, CH1_FREQ, CH2_FREQ, CH3_FREQ = (
    431.25,
    436.25,
    441.25,
    446.25,
)
# Backend
URL_ENDPOINT = 'https://foresteyes.iwing.in.th/'
AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InVuZHAycngiLCJyb2xlIjoicmFzUGkiLCJpYXQiOjE2MDg0NTA5NTJ9.tkgF8p4uOTuutdKZmC8Z0yghNHCmtvPnVncyz7vM6pQ'
RPI_ID = 2
CAM_ID = 2
