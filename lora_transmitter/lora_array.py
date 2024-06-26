import struct
import sys
import time
import asyncio
import os
from threading import Timer
sys.path.append('.')
sys.path.append('..')

import RPi.GPIO as GPIO
from SX127x.constants import *

import config

from lora import LoRa
from board import BaseBoard

SOURCE_DIR = './image_buffer/segmented/'
GENERATED_DATA_PKT_SIZE = config.PACKET_SIZE
SF = config.SF
CH0_FREQ = config.CH0_FREQ
CH1_FREQ = config.CH1_FREQ
CH2_FREQ = config.CH2_FREQ
CH3_FREQ = config.CH3_FREQ

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
loop = asyncio.get_event_loop()

CAM_MAC = config.CAM_MAC_ADDRESS

control_channel = 0
###########################################################
class Board0(BaseBoard):
    # Note that the BCM numbering for the GPIOs is used.
    DIO0    = 24
    DIO1    = 6
    RST     = 17
    LED     = 4
    SPI_BUS = 0
    SPI_CS  = 8

###########################################################
class Board1(BaseBoard):
    # Note that the BCM numbering for the GPIOs is used.
    DIO0    = 12
    DIO1    = 19
    RST     = 27
    LED     = None
    SPI_BUS = 0
    SPI_CS  = 20
        
###########################################################
class Board2(BaseBoard):
    # Note that the BCM numbering for the GPIOs is used.
    DIO0    = 25
    DIO1    = 13
    RST     = 23
    LED     = 18
    SPI_BUS = 0
    SPI_CS  = 7

#################################################
##Update Board3 is feedback channel
class Board3(BaseBoard):
    # Note that the BCM numbering for the GPIOs is used.
    DIO0    = 5
    DIO1    = 26
    RST     = 22
    LED     = None
    SPI_BUS = 0
    SPI_CS  = 21

#################################################
configs = [
    {'board':Board0, 'bw':BW.BW125, 'freq':CH0_FREQ, 'cr':CODING_RATE.CR4_8, 'sf':SF},
    {'board':Board1, 'bw':BW.BW125, 'freq':CH1_FREQ, 'cr':CODING_RATE.CR4_8, 'sf':SF},
    {'board':Board2, 'bw':BW.BW125, 'freq':CH2_FREQ, 'cr':CODING_RATE.CR4_8, 'sf':SF},
    {'board':Board3, 'bw':BW.BW125, 'freq':CH3_FREQ, 'cr':CODING_RATE.CR4_8, 'sf':SF},
]


for config in configs:
    board = config['board']
    GPIO.setup(board.SPI_CS, GPIO.OUT)
    GPIO.output(board.SPI_CS, GPIO.HIGH)
    board.setup()
    board.reset()

###########################################################
class mylora(LoRa):

    def __init__(self, board, verbose=False):
        super(mylora, self).__init__(board,verbose=verbose)
        self.board = board
        self.set_mode(MODE.SLEEP)
        self.feedback = False
        if board == Board3:
            self.set_dio_mapping([0] * 6)
            self.rx_avail = False
        else:
            self.set_dio_mapping([1, 0, 0, 0, 0, 0])    #1 for TxDone(table 63)
            self.queue_tx = asyncio.Queue(maxsize=1)
            self.tx_avail = True

    @property
    def name(self):
        return self.board.__name__

    def on_rx_done(self):
        self.rx_avail = True
        #print(self.get_irq_flags())
    
    def on_tx_done(self):
        #print("\nTxDone")
        #print(self.get_irq_flags())
        self.clear_irq_flags(TxDone=1)
        self.tx_avail = True
    
    def on_cad_done(self):
        print("\non_CadDone")
        print(self.get_irq_flags())

    def on_rx_timeout(self):
        print("\non_RxTimeout")
        print(self.get_irq_flags())

    def on_valid_header(self):
        print("\non_ValidHeader")
        print(self.get_irq_flags())

    def on_payload_crc_error(self):
        print("\non_PayloadCrcError")
        print(self.get_irq_flags())

    def on_fhss_change_channel(self):
        print("\non_FhssChangeChannel")
        print(self.get_irq_flags())
        

    async def startTX(self):
        send_packet = []  
        #CAM_MAC = config.CAM_MAC_ADDRESS
        cam_mac = bytes.fromhex(CAM_MAC.replace(':', ''))   
        print(f"[{self.name}] START")
        while True:
            while not self.feedback:
                await asyncio.sleep(0.001)
            payload = await self.queue_tx.get()
            await self.lora_tx(payload,0,0)
            await asyncio.sleep(3)

    async def startRX(self):
        send_packet = []  
        #CAM_MAC = config.CAM_MAC_ADDRESS
        cam_mac = bytes.fromhex(CAM_MAC.replace(':', ''))   
        print(f"[{self.name}] START")
        o_b = -1
        #feedback_channel = False
        
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        r_pack=[]
        
        while True:
            while not self.rx_avail:
                await asyncio.sleep(0.001)
            print('='*25,'feedback','='*25, time.ctime())
            self.rx_avail = False
            pkt_rssi,rssi = self.get_pkt_rssi_value(), self.get_rssi_value()
            payload = self.read_payload(nocheck=True)  # mean "do not check CRC!"
            print(f'payload is {payload}')
            self.clear_irq_flags(RxDone=1,PayloadCrcError=1)
            
            cam_mac_pack = list(payload[2:3])[0]
            
            if cam_mac_pack == 1:
                print(f'our cam_mac is {list(cam_mac)}')
                cam_rx = payload[4:]
                print(f'cam that rx recieve is is {cam_rx}')
                if bytes(cam_rx) != cam_mac:
                    loras[0].feedback = False
                    loras[1].feedback = False
                    loras[2].feedback = False
                    print(loras[0].feedback,loras[1].feedback,loras[2].feedback)
                    print('we must wait other to send')
                else:
                    loras[0].feedback = True
                    loras[1].feedback = True
                    loras[2].feedback = True
                    print("It's our turn!!! we are sending")
                    o_x = -99
                    o_y = -99
                    for b in range(3):
                        with open(f'./lora_receiver/rx_buffer/boardstatus/{b}.txt', "w") as f:
                            f.write(f'1_{time.time()}')
            elif cam_mac_pack == 2:
                if bytes(payload[4:]) == cam_mac:
                    print(f'fine! we re sending')
                else:
                    print('we must wait other to send')
            elif cam_mac_pack == 4:
                img_id = list(payload[4:6])
                img_id = img_id[0]*256 + img_id[1]
                print(list(payload[6:]))
                if os.path.isdir(f'./image_buffer/exported/{img_id}'):
                    if not os.path.exists(f'./image_buffer/segmented/{img_id}'):
                        os.mkdir(f'./image_buffer/segmented/{img_id}')
                npart = len(list(payload[6:]))
                print(npart)

                for i in range(0,npart,2):
                    x = int(list(payload[6+i:7+i])[0])
                    y = int(list(payload[7+i:8+i])[0])
                    print(x,y)
                    try:
                        os.rename(f'./image_buffer/exported/{img_id}/{x}_{y}.jpg',f'./image_buffer/segmented/{img_id}/{x}_{y}.jpg')
                    except:
                        print(f'not found {x}_{y}')
                
            elif list(payload[3:4])[0] == 1:
                if bytes(payload[4:]) == cam_mac:
                    loras[0].feedback = False
                    loras[1].feedback = False
                    loras[2].feedback = False
                else:
                    img_list = sorted(os.listdir(SOURCE_DIR))
                    for img_id in img_list:
                        if not os.path.isdir(f'{SOURCE_DIR}{img_id}'):
                            continue
                        await loras[0].lora_tx(cam_mac,1,0)
            elif loras[0].feedback or loras[1].feedback or loras[2].feedback:
                if list(payload[2:3])[0] == 0 and list(payload[3:4])[0] == 0:
                    img_id = list(payload[4:6])
                    img_id = img_id[0]*256 + img_id[1]
                    x = int(list(payload[6:7])[0])
                    y = int(list(payload[7:8])[0])
                    board_no = list(payload[8:9])
                    r_pack.append(f'{x}_{y}')
                    print('img_id',img_id,'x_y',x,y,board_no)
                    print(r_pack)
                    n_time = time.time()
                    b = board_no[0]
                    
                    if not os.path.isdir(f'./lora_receiver/rx_buffer/boardstatus'):
                        os.mkdir(f'./lora_receiver/rx_buffer/boardstatus/')
                    f  = open(f'./lora_receiver/rx_buffer/boardstatus/{b}.txt', "w")
                    f.write(f"1_{time.time()}")
                    f.close()
                    #update_wait(b)
                    #ได้ packet มาแล้วถ้ามีไฟล์ x_y ใน exported 
                    pkt_error = not self.rx_is_good()
                    self.clear_irq_flags(RxDone=1,PayloadCrcError=1)
                    try:
                        if os.path.isdir(f'/home/pi/Documents/forest-feedback-channel/image_buffer/segmented/{img_id}'):
                            os.rename(f'/home/pi/Documents/forest-feedback-channel/image_buffer/segmented/{img_id}/{x}_{y}.jpg', f'/home/pi/Documents/forest-feedback-channel/image_buffer/exported/{img_id}/{x}_{y}.jpg')
                            print(f'renamed /home/pi/Documents/forest-feedback-channel/image_buffer/segmented/{img_id}/{x}_{y}.jpg')
                        else:
                            print('not found file')
                    except:
                        print('not found file')
                    
            
                    '''
                    if os.path.isdir(f'/home/pi/Documents/forest-feedback-channel/image_buffer/segmented/{img_id}'):
                        os.rename(f'/home/pi/Documents/forest-feedback-channel/image_buffer/segmented/{img_id}/{x}_{y}.jpg', f'/home/pi/Documents/forest-feedback-channel/image_buffer/exported/{img_id}/{x}_{y}.jpg')
                        print(f'renamed /home/pi/Documents/forest-feedback-channel/image_buffer/segmented/{img_id}/{x}_{y}.jpg')
                    else:
                        print('not found file')
                    '''
                    if pkt_error:
                        print(f'[{self.name}] CRC ERROR (no data written)')
                        print(self.get_irq_flags())
                        print("Pkt RSSI: {} RSSI: {}".format(pkt_rssi,rssi))
                        print("GOt",img_id,x,y,board_no)
                        try:
                            if not os.path.isdir(f'./lora_receiver/error_buffer'):
                                os.mkdir(f'./lora_receiver/error_buffer')
                            if payload:
                                ts = int(time.time()*10000000)
                                with open(f'./lora_receiver/error_buffer/{self.name}.{ts}','wb') as f:
                                    f.write(bytearray(payload))
                        except Exception as e:
                            print("*** Exception2 {}".format(str(e)))
                        continue
                    else:
                        print("[{}] Receive: {} bytes (with header) from 0x{:02X} to 0x{:02X}".format(
                        self.name, len(payload), payload[1], payload[0]))
                        #print(payload)
                        print("Pkt RSSI: {} RSSI: {}".format(pkt_rssi,rssi))
                       
    async def tx_enqueue(self, payload):
        await self.queue_tx.put(payload)
        #payload=0_0_ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefgh

    async def lora_tx(self, payload, ask_send, fin_send, byte_payload = (__name__!='__main__')):
        # wait until ready for send(tx)
        while not self.tx_avail:
            await asyncio.sleep(0.001)
        
        self.tx_avail = False
        #The byte_payload condition is used to determine whether the payload is provided as a string or as a list of bytes. If byte_payload is False, it converts the payload string to a list of ASCII values using the to_ascii function.
        if fin_send:
            self.write_payload([
                0xff, # receiver (0xff for broadcast)
                0x80, # sender
                0x00,
                0x01,
                
            ] + (list(payload) if byte_payload else to_ascii(payload)))
            loras[0].feedback = False
            loras[1].feedback = False
            loras[2].feedback = False
        elif ask_send:
            self.write_payload([
                0xff, # receiver (0xff for broadcast)
                0x80, # sender
                0x01,
                0x00,
                
            ] + (list(payload) if byte_payload else to_ascii(payload)))
            
        else:
            self.write_payload([
                0xff, # receiver (0xff for broadcast)
                0x80, # sender
                0x00,
                0x00,
                
            ] + (list(payload) if byte_payload else to_ascii(payload)))
        #[0xff,ox80,...,payload]
        self.set_mode(MODE.TX)
        if not byte_payload:
            print(f"[{self.name}] TX:", ' '.join(f'{ord(x):02X}' for x in payload))
        else:
            print(f"[{self.name}] TX:", ' '.join(f'{x:02X}' for x in payload))

        #time.sleep(5) # there must be a better solution but sleep() works
        #loras[node].reset_ptr_rx()
        #loras[node].set_mode(MODE.RXCONT)
        print(f"[{self.name}] Sent")
       
        print('-'*50, time.ctime())
        await asyncio.sleep(0.1)

###########################################################
def set_feedback_channel():
    feedback_channel = True
def update_wait(b):
    b_active = [1,1,1]
    b_ltime[b] =[0,0,0]
    with open(f'./lora_receiver/rx_buffer/Board{b}', "r+") as f:
        w_time = int(f.read())
        w_time = w_time-5  if w_time>0 else 0
        f.seek(0)
        f.truncate()
        f.write(str(w_time))
    for j in range(3):
        if j!=b:
            ts = time.time()
            with open(f'./lora_receiver/rx_buffer/boardstatus/{j}.txt', "r") as f:
                i = f.read().split("_")
                b_active[j] = int(i[0])
                b_ltime[j] = float(i[1])
            with open(f'./lora_receiver/rx_buffer/Board{j}', "r+") as f:
                if ts-b_ltime[j]>100:
                    w_time = int(f.read())
                    w_time = w_time+5
                    f.seek(0)
                    f.truncate()
                    f.write(str(w_time))
def to_ascii(n):
    assert(type(n) == str)
    return [ord(c) for c in n]

def lora_teardown():
    for lora in loras:
        lora.set_mode(MODE.SLEEP)
        lora.board.teardown()

def lora_setup():
    for i in range(3):
        loop.create_task(loras[i].startTX())
    loop.create_task(loras[3].startRX())

###########################################################
loras = []
feedback_channel = False
for config in configs:
    board = config['board']
    lora = mylora(config['board'])
    lora.set_pa_dac(True)
    lora.set_pa_config(pa_select=1, output_power=15)
    lora.set_bw(config['bw'])
    lora.set_freq(config['freq'])
    lora.set_coding_rate(config['cr'])
    lora.set_spreading_factor(config['sf'])
    lora.set_rx_crc(True)
    lora.set_low_data_rate_optim(True)
    agc_auto_value = lora.get_agc_auto_on()
    print(f"AGC Auto Value: {agc_auto_value}")
    loras.append(lora)

async def enqueue():
    count = 0
    while True:
        # have module #0 broadcast a message 'Iwing' every 20 seconds
        #time.sleep(10)
        # for i in range(len(loras)):
        for i in range(4):
            payload = f'{count}_{i}_'+''.join(chr(x+65) for x in range(GENERATED_DATA_PKT_SIZE))
            #lora_tx(node = i, payload = '0'*count+str(count))
            #loras[i].lora_tx('0'*50+str(count))
            #loras[i].lora_tx(payload)
            await loras[i].tx_enqueue(payload)
            #print output
            #0_0_ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefgh
            #0_1_ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefgh
            #0_2_ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefgh
            #0_3_ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefgh
        count += 1

def non_active():
    print(" again sending")
    img_id=7
    allpicrecieve=os.listdir(f'./lora_receiver/rx_buffer/{7}')
    for x in range (0,len(allpicrecieve)//6):
        for y in range(0,6):
            if len(os.listdir(f'./lora_receiver/rx_buffer/7/{x}_{y}') )!= 0:
                os.rename(f'./image_buffer/exported/0007/{x}_{y}.jpg',f'./image_buffer/segmented/0007/{x}_{y}.jpg')
    loop.create_task(__main__.my_main())
    #loop.call_soon_threadsafe(loop.stop)

if __name__=='__main__':
    try:
        lora_setup()
        loop.create_task(enqueue())
        loop.run_forever()
    except KeyboardInterrupt:
        sys.stdout.flush()
        print("Exit")
        sys.stderr.write("KeyboardInterrupt\n")
    finally:
        sys.stdout.flush()
        print("Exit")
        lora_teardown()

