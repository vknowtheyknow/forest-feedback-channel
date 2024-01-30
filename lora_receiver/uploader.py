import json
import requests
import os
import datetime
import time
import sys
sys.path.append('.')
sys.path.append('..')

import config

url = config.URL_ENDPOINT
AUTH_TOKEN = config.AUTH_TOKEN
rpi_id = config.RPI_ID
cam_id = config.CAM_ID
header = {
    'Authorization': 'Bearer ' + AUTH_TOKEN
}


def upload_image(img_path):
    filename = time.strftime("%Y_%m_%d", time.localtime(time.time())) + '_' + img_path.split('/')[-1]
    files = {
        'file': ('image.jpg', open(img_path, 'rb'), 'image/jpeg')
    }
    data = {
        'rasPiId': rpi_id,
        'camId': cam_id,
        'sentAt': str(datetime.datetime.now()),
        'fileName': filename,
        'isHuman': False,
        'isWeapon': False,
        'isWildlife': False,
        'isDomestic': False
    }
    print('Posting Img:', filename, end=' ')
    r = requests.post(
        url + 'api/imgs/img_file',
        headers=header,
        files=files,
        data=data,
        timeout=10.0
    )
    print(r.status_code)
    if r.status_code == 201:
        os.rename(img_path, f'./lora_receiver/rx_buffer/uploaded/{filename}')
    return r.text


def upload_tx_status():
    print('Upload TX SP')
    try:
        # TX
        tx_sp_list = sorted(os.listdir('./service_packet_buffer/rx/received/'))
        if 'uploaded' in tx_sp_list:
            tx_sp_list.remove('uploaded')
        no_of_tx_sp = len(tx_sp_list)
        ind = 0
        payload = []
        pending_sp = []
        while ind < no_of_tx_sp:
            sp = tx_sp_list[ind]
            fn = f'./service_packet_buffer/rx/received/{sp}'
            print('TX_status:', sp)
            try:
                f = open(fn)
                sp_data = json.loads(f.read())
                f.close()
            except:
                print('Error open', fn)
                ind += 1
                continue
            payload.append({
                'loggedAt': str(datetime.datetime.fromtimestamp(float('.'.join(sp.split('.')[0:2])))),
                'rasPiType': 'tx',
                'rasPiId': rpi_id,
                'inputVoltage': sp_data['input_voltage'],
                'lastSentDate': str(datetime.datetime.fromtimestamp(int(sp_data['last_sent_time']))),
                'lastSentCamId': cam_id,
                'lastSentImgIndex': sp_data['last_sent_index'],
                'lastCamActiveDate': str(datetime.datetime.fromtimestamp(int(sp_data['camera_last_active']))),
                'lastReceivedCamId': cam_id,
                'lastReceivedImgIndex': sp_data['camera_index'],
                'temperature': sp_data['pi_temperature'],   # from RPI's CPU
                'envTemperature': sp_data['temperature'],   # from LM35
                'inputCurrent': sp_data['input_current'],
            })
            pending_sp.append(sp)
            if len(payload) < 20 and ind < (no_of_tx_sp - 1):
                ind += 1
                continue
            r = requests.post(
                url + 'api/logs/logs_data',
                headers=header,
                json=payload,
                timeout=10.0
            )
            if r.status_code == 201:
                file_list = {}
                for i in range(len(pending_sp)):
                    sp = pending_sp[i]
                    s_time = float('.'.join(sp.split('.')[:-1]))
                    payload[i]['time'] = s_time
                    s_time = time.strftime("%Y_%d_%m", time.localtime(s_time))
                    if s_time not in file_list:
                        file_list[s_time] = open(f'./service_packet_buffer/rx/received/uploaded/{s_time}.txt', 'a')
                    file_list[s_time].write(str(payload[i]).replace("'", '"')+'\n')
                    os.remove(f'./service_packet_buffer/rx/received/{sp}')
                for f in file_list:
                    file_list[f].close()
            print(r.text)
            payload = []
            pending_sp = []
            ind += 1
    except Exception as e:
        print('Error uploading service packets')
        print(e)


def upload_rx_status():
    print('Upload RX SP')
    try:
        # RX
        rx_sp_list = sorted(os.listdir('./service_packet_buffer/rx/rx/'))
        if 'uploaded' in rx_sp_list:
            rx_sp_list.remove('uploaded')
        no_of_rx_sp = len(rx_sp_list)
        ind = 0
        payload = []
        pending_sp = []
        while ind < no_of_rx_sp:
            sp = rx_sp_list[ind]
            fn = f'./service_packet_buffer/rx/rx/{sp}'
            print('RX_status:', sp)
            try:
                f = open(fn)
                sp_data = json.loads(f.read())
                f.close()
            except:
                print('Error open', fn)
                ind += 1
                continue
            payload.append({
                'loggedAt': str(datetime.datetime.fromtimestamp(float('.'.join(sp.split('.')[0:2])))),
                'rasPiType': 'rx',
                'rasPiId': rpi_id,
                'inputVoltage': round(sp_data['input_voltage'], 3),
                'lastReceivedDate': str(datetime.datetime.fromtimestamp(int(sp_data['last_receive_time']))),
                'lastReceivedCamId': cam_id,
                'lastReceivedImgIndex': sp_data['last_receive_index'],
                'temperature': round(sp_data['pi_temperature'], 2),   # from RPI's CPU
                'envTemperature': round(sp_data['temperature'], 2),   # from LM35
                'inputCurrent': round(sp_data['input_current'], 2),
            })
            pending_sp.append(sp)
            if len(payload) < 20 and ind < (no_of_rx_sp - 1):
                ind += 1
                continue
            r = requests.post(
                url + 'api/logs/logs_data',
                headers=header,
                json=payload,
                timeout=10.0
            )
            if r.status_code == 201:
                file_list = {}
                for i in range(len(pending_sp)):
                    sp = pending_sp[i]
                    s_time = float('.'.join(sp.split('.')[:-1]))
                    payload[i]['time'] = s_time
                    s_time = time.strftime("%Y_%d_%m", time.localtime(s_time))
                    if s_time not in file_list:
                        file_list[s_time] = open(f'./service_packet_buffer/rx/rx/uploaded/{s_time}.txt', 'a')
                    file_list[s_time].write(str(payload[i]).replace("'", '"')+'\n')
                    os.remove(f'./service_packet_buffer/rx/rx/{sp}')
                for f in file_list:
                    file_list[f].close()
            print(r.text)
            payload = []
            pending_sp = []
            ind += 1
    except Exception as e:
        print('Error uploading service packets')
        print(e)


if __name__ == '__main__':
    print('Manual uploading')
    upload_tx_status()
    upload_rx_status()
    RX_BUFFER = './lora_receiver/rx_buffer/'
    rx_buffer = os.listdir(RX_BUFFER)
    for image in sorted(rx_buffer):
        if os.path.isdir(f'{RX_BUFFER}/{image}'):
            continue
        print(upload_image(f'{RX_BUFFER}/{image}'))
