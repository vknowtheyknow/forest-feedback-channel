# for UNDP_1 device
print('UNDP_1')

# import sys
# sys.path.append('.')  #when run from ~/lora-multi-ch
# sys.path.append('..') #when run from module's dir
# import config

# rm config.py; ln -s ./config_files/undp1_config.py config.py

# Camera
CAM_MAC_ADDRESS = '00:62:4E:60:15:A1'
CAM_SSID = 'Campark-T86-d5bc52bb0144'
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
    432.5,
    437.5,
    442.5,
    447.5,
)
# Backend
URL_ENDPOINT = 'https://foresteyes.iwing.in.th/'
AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InVuZHAycngiLCJyb2xlIjoicmFzUGkiLCJpYXQiOjE2MDg0NTA5NTJ9.tkgF8p4uOTuutdKZmC8Z0yghNHCmtvPnVncyz7vM6pQ'
RPI_ID = 1
CAM_ID = 1
