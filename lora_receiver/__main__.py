import struct
import sys
import time
import os
import asyncio
from threading import Timer
sys.path.append('.')
sys.path.append('..')

import RPi.GPIO as GPIO
from SX127x.constants import *

import config
from lora import LoRa
from board import BaseBoard
import service_packet
import subprocess

#FEEDBACK = 0

MISS_IMG = './lora_receiver/miss_img/'

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
SF = config.SF
CH0_FREQ = config.CH0_FREQ
CH1_FREQ = config.CH1_FREQ
CH2_FREQ = config.CH2_FREQ
CH3_FREQ = config.CH3_FREQ
loop = asyncio.get_event_loop()

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
    board =  config['board']
    GPIO.setup(board.SPI_CS, GPIO.OUT)
    GPIO.output(board.SPI_CS, GPIO.HIGH)
    board.setup()
    board.reset()
    
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
    print('Sending:', img_id, x, y)

async def payload_enqueue(node_ind, payload):
    #print('payload_enqueue')
    await loras[node_ind].tx_enqueue(payload)

async def post_tx_status():
    #print('start post_tc_statas')
    sp_list = service_packet.generate_packet()
    for service_payload in sp_list:
        await asyncio.gather(
            payload_enqueue(3, [service_payload])
        )

def summit_lora_status(img_id):
    f = open('./lora_transmitter/.lora_status', 'w')
    f.write(f'{img_id}\n{round(time.time())}')
    f.close()
    os.rename('./lora_transmitter/.lora_status', './lora_transmitter/lora_status')


async def send_ack(payload,board):
    await post_tx_status()
    payload = payload + [board]
    await payload_enqueue(3, payload)
    await post_tx_status()
    #print('done')
    #lora_array.loop.call_soon_threadsafe(lora_array.loop.stop)    
def summit_lora_status(img_id):
    f = open('./lora_receiver/.lora_status', 'w')
    f.write(f'{img_id}\n{round(time.time())}')
    f.close()
    os.rename('./lora_receiver/.lora_status', './lora_receiver/lora_status')

def img_rx(payload):
    img_id = list(payload[0:2])
    img_id = img_id[0]*256 + img_id[1]
    x = int(list(payload[2:3])[0])
    y = int(list(payload[3:4])[0])
    sub_no = list(payload[4:6])
    sub_no = sub_no[0]*256 + sub_no[1]
    print('GOT:', img_id, x, y, sub_no)
    if img_id == 0 and x == 255 and y == 255:
        #print('Service packet:', end=' ')
        if sub_no == 0:
            #print('Tx Status')
            tx_sp = service_packet.unpack_service_packet(payload)
            #print(tx_sp)
        else:
            pass
        return None
    else:
        summit_lora_status(img_id)
    if not os.path.isdir(f'./lora_receiver/rx_buffer/{img_id}'):
        os.mkdir(f'./lora_receiver/rx_buffer/{img_id}')
    if not os.path.isdir(f'./lora_receiver/rx_buffer/{img_id}/{x}_{y}/'):
        os.mkdir(f'./lora_receiver/rx_buffer/{img_id}/{x}_{y}/')
    f = open(f'./lora_receiver/rx_buffer/{img_id}/{x}_{y}/{sub_no}', 'wb')
    f.write(bytes(payload[6:]))
    f.close()
    f = open(f'./lora_receiver/rx_buffer/{img_id}/.update.txt', 'w')
    f.write('1')
    f.close()
    os.rename(
        f'./lora_receiver/rx_buffer/{img_id}/.update.txt',
        f'./lora_receiver/rx_buffer/{img_id}/update.txt'
    )
    
###########################################################
class mylora(LoRa):

    def __init__(self, board, verbose=False):
        super(mylora, self).__init__(board,verbose=verbose)
        self.board = board
        self.set_mode(MODE.SLEEP)
        self.feedback = False
        if board == Board3:
            self.set_dio_mapping([1, 0, 0, 0, 0, 0])    #1 for TxDone(table 63)
            self.queue_tx = asyncio.Queue(maxsize=1)
            self.tx_avail = True
        else:
            self.set_dio_mapping([0] * 6)#on RXdone
        self.rx_avail = False
        

    @property
    def name(self):
        return self.board.__name__

    def on_rx_done(self):
        self.rx_avail = True

    def on_tx_done(self):
        #print("\nTxDone")
        #print(self.get_irq_flags())
        ##add
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
    '''    
    def all_recieved(self):
        self.feedback = True
    '''    
    async def tx_enqueue(self, payload):
        #print('tx_enque')
        await self.queue_tx.put(payload)

    async def lora_tx(self, payload,ask_send,fin_send):
        #print('lora_tx')
        while not self.tx_avail:
            await asyncio.sleep(0.001)
        #print(type(payload))
        self.tx_avail = False
        if ask_send==1:
            self.write_payload([
                0xff,  # receiver (0xff for broadcast)
                0x80,  # sender
                0x01,
                0x00,] 
             + list(payload) )
        elif ask_send==2:
            self.write_payload([
                0xff,  # receiver (0xff for broadcast)
                0x80,  # sender
                0x02,
                0x00,] 
             + list(payload) )
        elif ask_send==4:
            self.write_payload([
                0xff,  # receiver (0xff for broadcast)
                0x80,  # sender
                0x04,
                0x00,] 
             + list(payload) ) 
        elif fin_send:
            self.write_payload([
                0xff,  # receiver (0xff for broadcast)
                0x80,  # sender
                0x00,
                0x01,] 
             + list(payload) )
        else:
            self.write_payload([
                0xff,  # receiver (0xff for broadcast)
                0x80,  # sender
                0x00,
                0x00,] 
             + list(payload) )
        self.set_mode(MODE.TX)
        print(f"[{self.name}] TX:", ' '.join(f'{x:02X}' for x in payload))

        #time.sleep(5) # there must be a better solution but sleep() works
        #loras[node].reset_ptr_rx()
        #loras[node].set_mode(MODE.RXCONT)
        img_id = list(payload[0:2])
        img_id = img_id[0]*256 + img_id[1]
        subpic=[]
        for i in range(2,len(payload)-2,2):
            x = int(list(payload[i:i+1])[0])
            y = int(list(payload[i+1:i+2])[0])
            subpic.append(f'{x}_{y}')
        print(f"[{self.name}] Sent file_id :[{img_id}] recieved :{subpic}")
        print('-'*50, time.ctime())
        await asyncio.sleep(0.1)
     
    async def start(self):          
        print(f"[{self.name}] START")
        board = self.board
        o_x = -99
        o_y = -99
        o_img = -99
        o_payload = []
        sub_num = 0
        pack_success = 1
        o_cam = b''
        cam_q = []
        
        while True:
            
            if board == Board3:
                payloadACK = await loras[3].queue_tx.get()
                await loras[3].lora_tx(payloadACK,0,0)
                await asyncio.sleep(2)
               

            else:
                #print(0,1,2)
                '''
                t = Timer(300,self.all_recieved)
                t.start()
                '''
                self.reset_ptr_rx()
                self.set_mode(MODE.RXCONT) # Receiver mode
                while not self.rx_avail:
                    await asyncio.sleep(0.001)
                self.rx_avail = False
                self.board.led_on()
                #print("\nRxDone")
                print('-'*50, time.ctime())
                pkt_rssi,rssi = self.get_pkt_rssi_value(), self.get_rssi_value()
                payload = self.read_payload(nocheck=True)  # mean "do not check CRC!"
                #print(f'payload is {payload}')
                pkt_error = not self.rx_is_good()
                self.clear_irq_flags(RxDone=1,PayloadCrcError=1)
                
                if pkt_error:
                    print(f'[{self.name}] CRC ERROR (no data written)')
                    print("Pkt RSSI: {} RSSI: {}".format(pkt_rssi,rssi))
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
                    
                ask_send = list(payload[2:3])[0]
                fin_send = list(payload[3:4])[0]
                #print(f'ask state {ask_send}')
                #print(f'fin_state {fin_send}')
                if ask_send:
                    cam_id = payload[4:]
                    print('this is cam_q',end='|')
                    print(cam_q)
                    if len(cam_q)==0:
                        cam_q.append(cam_id)
                    if cam_q[0] == cam_id:
                        print(cam_q[0])
                        await loras[3].lora_tx(cam_id,1,0)
                    else:
                        #say everyone that it is sending which cam
                        await loras[3].lora_tx(cam_q[0],2,0)
                elif fin_send:
                    cam_mac = cam_q.pop(0)
                    cam_id = payload[4:]
                    if len(cam_q)==0:
                        await loras[3].lora_tx(cam_id,0,1)
                        subprocess.run(["python","./lora_receiver/merge.py"])
                        all_miss = os.listdir(f'{MISS_IMG}')
                        #print(allall_miss)
                        for i in all_miss:
                            f = open(f'{MISS_IMG}{i}/missing.txt', 'rb')
                            packet = f.read()
                            f.close()
                            print(f'failed packet : {packet}')
                            await loras[3].lora_tx(packet,4,0)
                            os.remove(f'{MISS_IMG}{i}/missing.txt')
                            os.rmdir(f'{MISS_IMG}{i}')
                            
                    
                    else:
                        await loras[3].lora_tx(cam_q[0],1,0)
                    
                    #the problem is board0 of rx may not available so we should send that it sended which packet
                
                else:
                    print("[{}] Receive: {} bytes (with header) from 0x{:02X} to 0x{:02X}".format(
                        self.name, len(payload), payload[1], payload[0]))
                    print("Pkt RSSI: {} RSSI: {}".format(pkt_rssi,rssi))
                    #[xx xx xx xx xx xx
                    packet_pointer = list(payload[4:5])[0]
                    img_id = list(payload[5:7])
                    img_id = img_id[0]*256 + img_id[1]
                    x = int(list(payload[7:8])[0])
                    y = int(list(payload[8:9])[0])
                    sub_no = list(payload[9:11])
                    sub_no = sub_no[0]*256 + sub_no[1]
                    
                    #send feedback
                    if(packet_pointer==0):
                        sub_num += 1
                    elif (packet_pointer==1):
                        sub_num = 0
                    elif (packet_pointer==2):
                        sub_num += 1
                        if pack_success:
                            await send_ack(payload[5:9],int(self.name[5]))#4 is packet_pointer, 5 6 is fileid, 7:x ,8:y ,9 10 is subno
                        pack_success = 1
                    if sub_no != sub_num:
                        pack_success = 0

                    
                    self.board.led_off()
                    # print("HEX:", ' '.join(f'{x:02X}' for x in payload[4:]))
                    # print("ASCII:", ''.join(chr(x) for x in payload[4:]))
                    try:
                        img_rx(payload[5:])
                    except Exception as e:
                        print("*** Exception {}".format(str(e)))  
                    '''
                    t.cancel()
                    t = Timer(300,self.all_recieved)
                    t.start()
                    '''
                



###########################################################

def to_ascii(n):
    assert(type(n) == str)
    return [ord(c) for c in n]


def lora_setup():
    for i in range(4):
        loop.create_task(loras[i].start())
    

def lora_teardown():
    for lora in loras:
        lora.set_mode(MODE.SLEEP)
        lora.board.teardown()



###########################################################
loras = []
for config in configs:
    board = config['board']
    lora = mylora(config['board'])
    lora.set_pa_config(pa_select=1, max_power=21, output_power=15)
    lora.set_bw(config['bw'])
    lora.set_freq(config['freq'])
    lora.set_coding_rate(config['cr'])
    lora.set_spreading_factor(config['sf'])
    lora.set_rx_crc(True)
    lora.set_low_data_rate_optim(True)
    assert(lora.get_agc_auto_on() == 1)
    loras.append(lora)

if __name__=='__main__':
    try:
        lora_setup()
        #loop.create_task(my_main())
        loop.run_forever()
    except KeyboardInterrupt:
        sys.stdout.flush()
        print("Exit")
        sys.stderr.write("KeyboardInterrupt\n")
    finally:
        sys.stdout.flush()
        print("Exit")
        lora_teardown()

