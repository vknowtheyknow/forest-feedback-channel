# for UNDP_3 device
print('UNDP_3')

# import sys
# sys.path.append('.')  #when run from ~/lora-multi-ch
# sys.path.append('..') #when run from module's dir
# import config

# rm config.py; ln -s ./config_files/undp3_config.py config.py

# Camera
CAM_MAC_ADDRESS = '62:00:a1:14:b3:de'
CAM_SSID = 'Campark-T86-5a8230bb0144'
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
    443.75,
    448.75,
    433.75,
    438.75,
)

# Backend
URL_ENDPOINT = 'https://foresteyes.iwing.in.th/'
AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InVuZHAzcngiLCJyb2xlIjoicmFzUGkiLCJpYXQiOjE2MDg0NTEwMTJ9.INkl1TXf-g2DUkjPcwheIboaB4wTlyfvfHFPblEUkjU'
RPI_ID = 3
CAM_ID = 3
