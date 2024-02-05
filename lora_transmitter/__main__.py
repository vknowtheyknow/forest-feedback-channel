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
#import boardstatus
PACKET_SIZE = config.PACKET_SIZE
SOURCE_DIR = './image_buffer/segmented/'
EXPORTED_DIR = './image_buffer/exported/'

async def payload_enqueue_wrapper(index, payload_list, active):
    print(f'this is from payload wrapper {active}')
    if active:
        await payload_enqueue(index, payload_list)
        
def payload_prep(file_id, seg_name):
    if not seg_name:
        return []
    f = open(f'{SOURCE_DIR}{file_id}/{seg_name}', 'rb')
    #f = './image_buffer/segmented/00010/1_0.jpg'
    file_id = int(file_id)
    #file_id = 10
    ori_b = f.read()
    f.close()
    #add
    #seg_name = '1_0.jpg'
    #print(seg_name.split('.'))
    #>['1_0', 'jpg']
    #
    x, y = [int(i) for i in seg_name.split('.')[0].split('_')]
    
    #print(f'x:{x},y:{y}')
    #>x:1,y:0
    
    header = bytes([file_id//256, file_id%256, x, y])
    #>b'\x00\n\x01\x00'
    sub_no = 0
    payload_list = []
    while(ori_b):
        subheader = bytes([sub_no//256, sub_no%256])
        #sub_no=2
        #b'\x00\x02'
        payload = header + subheader + ori_b[:PACKET_SIZE]
        #b'\x00\n\x01\x00\x00\x02'+binary_img
        payload_list.append(payload)
        sub_no += 1
        ori_b = ori_b[PACKET_SIZE:]
        #print(payload_list)
    return payload_list

def print_header(payload):
    #payload =b'\x00\n\x01\x00\x00\x02'+binary_img
    img_id = list(payload[0:2])
    img_id = img_id[0]*256 + img_id[1]
    x = int(list(payload[2:3])[0])
    y = int(list(payload[3:4])[0])
    sub_no = list(payload[4:6])
    sub_no = sub_no[0]*256 + sub_no[1]
    print('Sending:', img_id, x, y, sub_no)
    #2| Sending: 10 8 1 20

async def payload_enqueue(node_ind, payload_list):
    #print(payload_list)
    for payload in payload_list:
        #add
        #print(f'payload:{payload}')
        #
        print(node_ind, end = '| ')
        print_header(payload)
        await lora_array.loras[node_ind].tx_enqueue(payload)

async def post_tx_status():
    # Generate service packets using the generate_packet function
    sp_list = service_packet.generate_packet()
    for service_payload in sp_list:
        # Use asyncio.gather to concurrently(in the same time) enqueue payloads for all four modules
        print(f'service payload is [{service_payload}]')
        await asyncio.gather(
            payload_enqueue(0, [service_payload]),
            payload_enqueue(1, [service_payload]),
            payload_enqueue(2, [service_payload]),
            
        )

def summit_lora_status(img_id):
    f = open('./lora_transmitter/.lora_status', 'w')
    f.write(f'{img_id}\n{round(time.time())}')
    f.close()
    os.rename('./lora_transmitter/.lora_status', './lora_transmitter/lora_status')

async def my_main():
    SOURCE_DIR = './image_buffer/segmented/'
    EXPORTED_DIR = './image_buffer/exported/'
    CAM_MAC = '00:62:4E:60:15:A1'
    cam_mac = bytes.fromhex(CAM_MAC.replace(':', ''))
    print(f'cam_mac is {cam_mac}')
    '''
    if 'boardstatus' in sys.modules:   # Check if "rand_gen" is cached
        sys.modules.pop('boardstatus')  # If yes, remove it
    import boardstatus
    '''
    if not os.path.isdir(f'./lora_receiver/rx_buffer/boardstatus'):
        os.mkdir(f'./lora_receiver/rx_buffer/boardstatus')
    for b in range(3):
        with open(f'./lora_receiver/rx_buffer/boardstatus/{b}.txt', "w") as f:
            f.write(f'1_{time.time()}')
        
    
    
    #os.listdir(path) = Get the list of all files and directories 
    #SOURCE_DIR = './image_buffer/segmented/'==>00010 00001 00020 etc.
    img_list = sorted(os.listdir(SOURCE_DIR))
    node_ord = 0
    b_active = [1,1,1]
    ts = time.time()
    b_ltime = [ts,ts,ts]
    #sp_list = service_packet.generate_packet()
    #print(f'sp_list is {sp_list}')
    #old context
    #await post_tx_status()
    for img_id in img_list:
        
        await lora_array.loras[0].lora_tx(cam_mac,1,0)
        print(img_id)
        if not os.path.isdir(f'{SOURCE_DIR}{img_id}'):
            continue
        seg_list = os.listdir(SOURCE_DIR + img_id)
        
        #random.shuffle(seg_list)
        if not os.path.isdir(f'{EXPORTED_DIR}{img_id}'):
            os.mkdir(f'{EXPORTED_DIR}{img_id}')
        last_seg = len(seg_list)
        #time.start()
        while last_seg>0:
            ts = time.time()
            for b in range(3):
                with open(f'./lora_receiver/rx_buffer/boardstatus/{b}.txt', "r") as f:
                    i = f.read().split("_")
                    b_active[b] = int(i[0])
                    b_ltime[b] = float(i[1])
                if ts - b_ltime[b] > 60:
                    with open(f'./lora_receiver/rx_buffer/boardstatus/{b}.txt', "w") as f:
                        f.write(f'0_{b_ltime[b]}')
                    
            print(b_ltime[0])
            print(b_ltime[1])
            print(b_ltime[2])
            b_active_num = b_active[0]+b_active[1]+b_active[2]
            seg_ind = 0
            ###########why we have
            seg_list.extend(5*[False])

            while seg_ind < last_seg:
                for b in range(3):
                    with open(f'./lora_receiver/rx_buffer/boardstatus/{b}.txt', "r") as f:
                        i = f.read().split("_")
                        b_active[b] = int(i[0])
                        b_ltime[b] = float(i[1])
                        print(b_active[b])
                        print(b_ltime[b])
                    if ts - b_ltime[b] > 60:
                        with open(f'./lora_receiver/rx_buffer/boardstatus/{b}.txt', "w") as f:
                            f.write(f'0_{b_ltime[b]}')
                if b_active[0]==1:
                    payload_list_0 = payload_prep(img_id, seg_list[seg_ind])
                    seg_ind +=1
                if b_active[1]==1:
                    payload_list_1 = payload_prep(img_id, seg_list[seg_ind+1])
                    seg_ind +=1
                if b_active[2]==1:
                    payload_list_2 = payload_prep(img_id, seg_list[seg_ind+2])
                    seg_ind +=1
                
                await asyncio.gather(
                    *[payload_enqueue_wrapper(0, payload_list_0,b_active[0]),
                    payload_enqueue_wrapper(1, payload_list_1,b_active[1]),
                    payload_enqueue_wrapper(2, payload_list_2,b_active[2])]
                )
                
                summit_lora_status(img_id)
            
            seg_list = os.listdir(SOURCE_DIR + img_id)
            last_seg = len(seg_list)
            print(f'this is file that send unsuccessfully ,amount:{last_seg} which are {seg_list}')
            
        if len(seg_list) == 0:
            await lora_array.loras[0].lora_tx(b'',0,1)
            os.rmdir(SOURCE_DIR + img_id)
            
    await post_tx_status()
    print('done')
    #lora_array.loop.call_soon_threadsafe(lora_array.loop.stop)
            
lora_array.lora_setup()
lora_array.loop.create_task(my_main())
lora_array.loop.run_forever()
