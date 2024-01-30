import ads1115
import time
import pexpect
import json
import sys
import os

sp_structure = {
    'tx': [
        ['input_voltage', 2],
        ['camera_index', 2],
        ['camera_last_active', 4],
        ['last_sent_index', 2],
        ['last_sent_time', 4],
        ['pi_temperature', 2],
        ['input_current', 2],
        ['temperature', 2],
    ],
    'rx': [
        ['input_voltage', 2],
        ['last_receive_index', 2],
        ['last_receive_time', 4],
        ['pi_temperature', 2],
        ['input_current', 2],
        ['temperature', 2],
    ]
}

def get_temp():
    child = pexpect.spawn('vcgencmd measure_temp')
    child.expect('temp=')
    raw = child.read()
    temp = str(raw).split('\'')[0][2:]
    print(f"Temp: {temp}'C")
    return float(temp)

def get_camera_status():    #for TX only
    f = open('./image_buffer/camera_status')
    camera_status = f.read().split('\n')
    f.close()
    return [int(camera_status[i]) for i in range(2)]

def get_lora_last_sent():   #for TX only
    f = open('./lora_transmitter/lora_status')
    lora_status = f.read().split('\n')
    f.close()
    return [int(lora_status[i]) for i in range(2)]

def get_lora_last_receive():    #for RX only
    f = open('./lora_receiver/lora_status')
    lora_status = f.read().split('\n')
    f.close()
    return [int(lora_status[i]) for i in range(2)]

def prepare_data(sender):
    ads1115_data = ads1115.read_voltage()
    if sender == 'tx':
        service_data = {}
        service_data['input_voltage'] = ads1115_data[0]
        service_data['camera_index'], service_data['camera_last_active'] = get_camera_status()
        service_data['last_sent_index'], service_data['last_sent_time'] = get_lora_last_sent()
        service_data['pi_temperature'] = get_temp()
        service_data['input_current'] = ads1115_data[1]
        service_data['temperature'] = ads1115_data[2]
        return service_data
    else:   #sender == 'rx'
        service_data = {}
        service_data['input_voltage'] = ads1115_data[0]
        service_data['last_receive_index'], service_data['last_receive_time'] = get_lora_last_receive()
        service_data['pi_temperature'] = get_temp()
        service_data['input_current'] = ads1115_data[1]
        service_data['temperature'] = ads1115_data[2]
        return service_data

def generate_packet():    #for TX only
    sv_header = bytes([0,0,255,255,0,0])
    sp_list = []
    tx_sp_list = sorted(os.listdir('./service_packet_buffer/tx/'))
    if 'transmitted' in tx_sp_list:
        tx_sp_list.remove('transmitted')
    file_list = {}
    for fn in tx_sp_list:
        try:
            f = open(f'./service_packet_buffer/tx/{fn}')
            service_data = json.loads(f.read())
            f.close()
            s_time = float('.'.join(fn.split('.')[:-1]))
            s_time = time.strftime("%Y_%d_%m", time.localtime(s_time))
            if s_time not in file_list:
                file_list[s_time] = open(f'./service_packet_buffer/tx/transmitted/{s_time}.txt', 'a')
            file_list[s_time].write(str(service_data).replace("'", '"')+'\n')
            os.remove(f'./service_packet_buffer/tx/{fn}')
        except Exception as e:
            print('Error open', fn)
            print(e)
            continue
        service_data['input_voltage'] = round(service_data['input_voltage'] * 1000)
        service_data['pi_temperature'] = round(service_data['pi_temperature'] * 10)
        service_data['input_current'] = round(service_data['input_current'] * 10000)
        service_data['temperature'] = round(service_data['temperature'] * 10)
        payload = b''
        for i in sp_structure['tx']:
            service, size = i
            payload += service_data[service].to_bytes(size, byteorder='big')
        sp_list.append(sv_header + payload)
    for f in file_list:
        file_list[f].close()
    return sp_list

def unpack_service_packet(packet_data): #for RX only
    packet_data = list(packet_data)[6:]
    service_data = {'time': time.time()}
    etime = service_data['time']
    for i in sp_structure['tx']:
        service, size = i
        service_data[service] = int.from_bytes(packet_data[:size], byteorder='big')
        packet_data = packet_data[size:]
    service_data['input_voltage'] = service_data['input_voltage'] / 1000
    service_data['pi_temperature'] = service_data['pi_temperature'] / 10
    service_data['input_current'] = service_data['input_current'] / 10000
    service_data['temperature'] = service_data['temperature'] / 10
    service_data['time'] = time.ctime(service_data['time'])
    f = open(f'./service_packet_buffer/rx/received/.{etime}.json', 'w')
    f.write(str(service_data).replace("'", '"'))
    f.close()
    os.rename(
        f'./service_packet_buffer/rx/received/.{etime}.json',
        f'./service_packet_buffer/rx/received/{etime}.json'
    )
    return service_data

def log_to_file(device):
    if device == 'tx':
        print('Logging Tx Status')
        tx_sp = prepare_data('tx')
        tx_sp['time'] = time.time()
        etime = tx_sp['time']
        f = open(f'./service_packet_buffer/tx/.{etime}.json', 'w')
        tx_sp['time'] = time.ctime(tx_sp['time'])
        f.write(str(tx_sp).replace("'", '"'))
        f.close()
        os.rename(
            f'./service_packet_buffer/tx/.{etime}.json',
            f'./service_packet_buffer/tx/{etime}.json'
        )
        return tx_sp
    else:
        print('Logging Rx Status')
        rx_sp = prepare_data('rx')
        rx_sp['time'] = time.time()
        etime = rx_sp['time']
        f = open(f'./service_packet_buffer/rx/rx/.{etime}.json', 'w')
        rx_sp['time'] = time.ctime(rx_sp['time'])
        f.write(str(rx_sp).replace("'", '"'))
        f.close()
        os.rename(
            f'./service_packet_buffer/rx/rx/.{etime}.json',
            f'./service_packet_buffer/rx/rx/{etime}.json'
        )
        return rx_sp
    
if __name__=='__main__':
    print(sys.argv[1])
    sp_data = log_to_file(sys.argv[1])
    sp_data = json.dumps(sp_data, sort_keys=True, indent=4, separators=(',', ':'))
    print(sp_data)
    
