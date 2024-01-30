import os
import time
import random
import asyncio
import sys
sys.path.append('.')
sys.path.append('..')

import config
import lora_array
import service_packet

PACKET_SIZE = config.PACKET_SIZE
SOURCE_DIR = './image_buffer/segmented/'
EXPORTED_DIR = './image_buffer/exported/'

def payload_prep(file_id, seg_name):
    if not seg_name:
        return []
    f = open(f'{SOURCE_DIR}{file_id}/{seg_name}', 'rb')
    file_id = int(file_id)
    ori_b = f.read()
    f.close()
    x, y = [int(i) for i in seg_name.split('.')[0].split('_')]
    header = bytes([file_id//256, file_id%256, x, y])
    sub_no = 0
    payload_list = []
    while(ori_b):
        subheader = bytes([sub_no//256, sub_no%256])
        payload = header + subheader + ori_b[:PACKET_SIZE]
        payload_list.append(payload)
        sub_no += 1
        ori_b = ori_b[PACKET_SIZE:]
    return payload_list

def print_header(payload):
    img_id = list(payload[0:2])
    img_id = img_id[0]*256 + img_id[1]
    x = int(list(payload[2:3])[0])
    y = int(list(payload[3:4])[0])
    sub_no = list(payload[4:6])
    sub_no = sub_no[0]*256 + sub_no[1]
    print('Sending:', img_id, x, y, sub_no)

async def payload_enqueue(node_ind, payload_list):
    for payload in payload_list:
        print(node_ind, end = '| ')
        print_header(payload)
        await lora_array.loras[node_ind].tx_enqueue(payload)

async def post_tx_status():
    sp_list = service_packet.generate_packet()
    for service_payload in sp_list:
        await asyncio.gather(
            payload_enqueue(0, [service_payload]),
            payload_enqueue(1, [service_payload]),
            payload_enqueue(2, [service_payload]),
            payload_enqueue(3, [service_payload])
        )

def summit_lora_status(img_id):
    f = open('./lora_transmitter/.lora_status', 'w')
    f.write(f'{img_id}\n{round(time.time())}')
    f.close()
    os.rename('./lora_transmitter/.lora_status', './lora_transmitter/lora_status')

async def my_main():
    img_list = sorted(os.listdir(SOURCE_DIR))
    node_ord = 0
    await post_tx_status()
    for img_id in img_list:
        print(img_id)
        if not os.path.isdir(f'{SOURCE_DIR}{img_id}'):
            continue
        seg_list = os.listdir(SOURCE_DIR + img_id)
        random.shuffle(seg_list)
        if not os.path.isdir(f'{EXPORTED_DIR}{img_id}'):
            os.mkdir(f'{EXPORTED_DIR}{img_id}')
        last_seg = len(seg_list)
        seg_list.extend([False, False, False, False])
        for seg_ind in range(0, last_seg+1, 4):
            payload_list_0 = payload_prep(img_id, seg_list[seg_ind])
            payload_list_1 = payload_prep(img_id, seg_list[seg_ind+1])
            payload_list_2 = payload_prep(img_id, seg_list[seg_ind+2])
            payload_list_3 = payload_prep(img_id, seg_list[seg_ind+3])
            await asyncio.gather(
                payload_enqueue(0, payload_list_0),
                payload_enqueue(1, payload_list_1),
                payload_enqueue(2, payload_list_2),
                payload_enqueue(3, payload_list_3)
            )
            summit_lora_status(img_id)
            for i in range(4):
                if seg_list[seg_ind+i]:
                    os.rename(f'{SOURCE_DIR}{img_id}/{seg_list[seg_ind+i]}', f'{EXPORTED_DIR}{img_id}/{seg_list[seg_ind+i]}')

        seg_list = os.listdir(SOURCE_DIR + img_id)
        if len(seg_list) == 0:
            os.rmdir(SOURCE_DIR + img_id)
    await post_tx_status()
    print('done')
    #lora_array.loop.call_soon_threadsafe(lora_array.loop.stop)
            
lora_array.lora_setup()
lora_array.loop.create_task(my_main())
lora_array.loop.run_forever()