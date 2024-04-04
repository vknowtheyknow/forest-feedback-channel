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
    packet_pointer = bytes([1])
    header = bytes([file_id//256, file_id%256, x, y])
    #>b'\x00\n\x01\x00'
    sub_no = 0
    payload_list = []
    while(ori_b):
        subheader = bytes([sub_no//256, sub_no%256])
        #sub_no=2
        #b'\x00\x02'
        payload = packet_pointer+header + subheader + ori_b[:PACKET_SIZE]
        #b'\x00\n\x01\x00\x00\x02'+binary_img
        payload_list.append(payload)
        sub_no += 1
        ori_b = ori_b[PACKET_SIZE:]
        packet_pointer = bytes([0])
        if len(ori_b) <= PACKET_SIZE:
            packet_pointer = bytes([2])
        #print(payload_list)
    #sub_no_{x}_{y} = sub_no-1
    return payload_list

def print_header(payload):
    #payload =b'\x00\n\x01\x00\x00\x02'+binary_img
    img_id = list(payload[1:3])
    img_id = img_id[0]*256 + img_id[1]
    x = int(list(payload[3:4])[0])
    y = int(list(payload[4:5])[0])
    sub_no = list(payload[5:7])
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
        '''
        st=time.time()
        await asyncio.sleep(w_time)
        print(time.time()-st)
        '''
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
    while True:
        SOURCE_DIR = './image_buffer/segmented/'
        EXPORTED_DIR = './image_buffer/exported/'
        CAM_MAC = config.CAM_MAC_ADDRESS
        cam_mac = bytes.fromhex(CAM_MAC.replace(':', ''))
        print(f'cam_mac is {cam_mac}')
        '''
        if 'boardstatus' in sys.modules:   # Check if "rand_gen" is cached
            sys.modules.pop('boardstatus')  # If yes, remove it
        import boardstatus
        '''
        if not os.path.isdir(f'./lora_receiver/rx_buffer/boardstatus'):
            os.mkdir(f'./lora_receiver/rx_buffer/boardstatus')
        
            
        
        
        #os.listdir(path) = Get the list of all files and directories 
        #SOURCE_DIR = './image_buffer/segmented/'==>00010 00001 00020 etc.
        img_list = sorted(os.listdir(SOURCE_DIR))
        print(f'img_list| {img_list}')
        
        node_ord = 0
        b_active = [1,1,1]
        ts = time.time()
        b_ltime = [ts,ts,ts]
        
        #sp_list = service_packet.generate_packet()
        #print(f'sp_list is {sp_list}')
        #old context
        #await post_tx_status()
        for img_id in img_list:
            st_img = time.time()
            for b in range(3):
                with open(f'./lora_receiver/rx_buffer/boardstatus/{b}.txt', "w") as f:
                    f.write(f'1_{st_img}')
            #await payload_enqueue_wrapper(0, cam_mac,1)
            if not os.path.isdir(f'{SOURCE_DIR}{img_id}'):
                continue
            seg_list = os.listdir(SOURCE_DIR + img_id)
            last_seg = len(seg_list)
            if last_seg ==0:
                continue
            await lora_array.loras[0].lora_tx(cam_mac,1,0)
            
            '''
            t.start()
            if feedback != 2 then
            waiting 15 minute
            '''
            
            await asyncio.sleep(5)
            print(img_id)
            
            
            #random.shuffle(seg_list)
            if not os.path.isdir(f'{EXPORTED_DIR}{img_id}'):
                os.mkdir(f'{EXPORTED_DIR}{img_id}')
            
            #time.start()
            while last_seg>0:
                ts = time.time()
                for b in range(3):
                    with open(f'./lora_receiver/rx_buffer/boardstatus/{b}.txt', "r") as f:
                        i = f.read().split("_")
                        b_active[b] = int(i[0])
                        b_ltime[b] = float(i[1])
                        
               
                #seg_list.extend(5*[False])
                payload_list_0 = b''
                payload_list_1 = b''
                payload_list_2 = b''
                seg_ind = 0
                while seg_ind < last_seg:
                    for b in range(3):
                        print(f'last active is {ts-b_ltime[b]}')
                        if ts - b_ltime[b] > 120:
                            with open(f'./lora_receiver/rx_buffer/boardstatus/{b}.txt', "w") as f:
                                f.write(f'0_{b_ltime[b]}')
                                b_active[b]=0
                        
                        if ts - b_ltime[b] > 360:
                            with open(f'./lora_receiver/rx_buffer/boardstatus/{b}.txt', "w") as f:
                                f.write(f'1_{ts}')
                                b_active[b]=1
                        
                    #print(f'seg_list is {seg_list},1:{seg_list[seg_ind]},2:{seg_list[seg_ind+1]},3:{seg_list[seg_ind+2]}')
                    
                    payload_list_0 = payload_prep(img_id, seg_list[seg_ind])
                    seg_ind +=1
                    try:
                        payload_list_1 = payload_prep(img_id, seg_list[seg_ind])
                        seg_ind +=1
                    except:
                        print(f'not found seglist[{seg_ind}]')
                        b_active[1]=0
                    try:
                        payload_list_2 = payload_prep(img_id, seg_list[seg_ind])
                        seg_ind +=1
                    except:
                        print(f'not found seglist[{seg_ind}]')
                        b_active[2]=0

                    
                    
                    bg=time.time()
                    print(f'before gather{bg}')
                    
                    await asyncio.gather(
                        *[payload_enqueue_wrapper(0, payload_list_0,b_active[0]),
                        payload_enqueue_wrapper(1, payload_list_1,b_active[1]),
                        payload_enqueue_wrapper(2, payload_list_2,b_active[2])]
                    )
                    
                    print(f'after gather{time.time()-bg}')
                    
                    summit_lora_status(img_id)
                    ts = time.time()
                    for b in range(3):
                        with open(f'./lora_receiver/rx_buffer/boardstatus/{b}.txt', "r") as f:
                            i = f.read().split("_")
                            b_active[b] = int(i[0])
                            b_ltime[b] = float(i[1])
                #await asyncio.sleep(30)
                if seg_ind>=last_seg:
                    last_seg = 0
                    break
                
            seg_list = os.listdir(SOURCE_DIR + img_id)
            last_seg = len(seg_list)
            print(f'this is file that send unsuccessfully ,amount:{last_seg} which are {seg_list}')
            
            if len(seg_list) == 0:
                await asyncio.sleep(10)
                await lora_array.loras[0].lora_tx(cam_mac,0,1)
                os.rmdir(SOURCE_DIR + img_id)
                et_img = time.time()
                print(f'use {(et_img-st_img)//60} minutes to send picture')
            
        await post_tx_status()
        await asyncio.sleep(40)  
        print('done')
        #lora_array.loop.call_soon_threadsafe(lora_array.loop.stop)

if __name__=='__main__':
    try:
        lora_array.lora_setup()
        lora_array.loop.create_task(my_main())
        lora_array.loop.run_forever()
    except KeyboardInterrupt:
        sys.stdout.flush()
        print("Exit")
        sys.stderr.write("KeyboardInterrupt\n")
        
