import struct
import sys
import time
import os
import asyncio
sys.path.append('.')
sys.path.append('..')

import RPi.GPIO as GPIO
from SX127x.constants import *

import config
from lora import LoRa
from board import BaseBoard
import service_packet

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
        self.set_dio_mapping([0] * 6)
        self.rx_avail = False

    @property
    def name(self):
        return self.board.__name__

    def on_rx_done(self):
        self.rx_avail = True

    def on_tx_done(self):
        print("\nTxDone")
        print(self.get_irq_flags())

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

    async def start(self):          
        print(f"[{self.name}] START")
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT) # Receiver mode
        while True:
            while not self.rx_avail:
                await asyncio.sleep(0.001)
            self.rx_avail = False
            self.board.led_on()
            #print("\nRxDone")
            pkt_rssi,rssi = self.get_pkt_rssi_value(), self.get_rssi_value()
            payload = self.read_payload(nocheck=True)  # mean "do not check CRC!"
            pkt_error = not self.rx_is_good()
            self.clear_irq_flags(RxDone=1,PayloadCrcError=1)
            print('-'*50, time.ctime())
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
            print("[{}] Receive: {} bytes (with header) from 0x{:02X} to 0x{:02X}".format(
                self.name, len(payload), payload[1], payload[0]))
            print("Pkt RSSI: {} RSSI: {}".format(pkt_rssi,rssi))
            self.board.led_off()
            # print("HEX:", ' '.join(f'{x:02X}' for x in payload[4:]))
            # print("ASCII:", ''.join(chr(x) for x in payload[4:]))
            try:
                img_rx(payload[4:])
            except Exception as e:
                print("*** Exception {}".format(str(e)))

###########################################################

def to_ascii(n):
    assert(type(n) == str)
    return [ord(c) for c in n]

def lora_tx(payload, node = 0):
    loras[node].write_payload([
        0xff, # receiver (0xff for broadcast)
        0x80, # sender
        0x00, # ???
        0x00, # ???
    ] + to_ascii(payload))
    loras[node].set_mode(MODE.TX)
    time.sleep(3) # there must be a better solution but sleep() works
    loras[node].reset_ptr_rx()
    loras[node].set_mode(MODE.RXCONT)
    print('-'*50)
    print(f'[{loras[node].name}] Sent: {payload[:min(10, len(payload))]}')
    sys.stderr.write(f'[{loras[node].name}] Sent: {payload[:min(10, len(payload))]}')

def lora_setup():
    for lora in loras:
        loop.create_task(lora.start())

def lora_teardown():
    for lora in loras:
        lora.set_mode(MODE.SLEEP)
        lora.board.teardown()

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
        print('Service packet:', end=' ')
        if sub_no == 0:
            print('Tx Status')
            tx_sp = service_packet.unpack_service_packet(payload)
            print(tx_sp)
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
        loop.run_forever()
    except KeyboardInterrupt:
        sys.stdout.flush()
        print("Exit")
        sys.stderr.write("KeyboardInterrupt\n")
    finally:
        sys.stdout.flush()
        print("Exit")
        lora_teardown()

