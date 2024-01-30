import struct
import sys
import time
import asyncio
from threading import Timer
sys.path.append('.')
sys.path.append('..')

import RPi.GPIO as GPIO
from SX127x.constants import *

import config
from lora import LoRa
from board import BaseBoard

GENERATED_DATA_PKT_SIZE = config.PACKET_SIZE
SF = config.SF
CH0_FREQ = config.CH0_FREQ
CH1_FREQ = config.CH1_FREQ
CH2_FREQ = config.CH2_FREQ
CH3_FREQ = config.CH3_FREQ

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
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
        self.set_dio_mapping([1, 0, 0, 0, 0, 0])    #1 for TxDone(table 63)
        self.queue_tx = asyncio.Queue(maxsize=1)
        self.tx_avail = True

    @property
    def name(self):
        return self.board.__name__

    def on_rx_done(self):
        if self.get_irq_flags()['crc_error']:
            return None
        self.board.led_on()
        #print("\nRxDone")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        print('-'*50, time.ctime())
        print("[{}] Receive: {} bytes (with header) from 0x{:02X} to 0x{:02X}".format(
            self.name, len(payload), payload[1], payload[0]))
        print("Pkt RSSI: {} RSSI: {}".format(self.get_pkt_rssi_value(), self.get_rssi_value()))
        self.board.led_off()
        print("HEX:", ' '.join(f'{x:02X}' for x in payload[4:]))
        print("ASCII:", ''.join(chr(x) for x in payload[4:]))

    def on_tx_done(self):
        # print("\nTxDone")
        # print(self.get_irq_flags())
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

    async def start(self):          
        print(f"[{self.name}] START")
        t = Timer(300.0, non_active)
        t.start()
        while True:
            payload = await self.queue_tx.get()
            await self.lora_tx(payload)
            t.cancel()
            t = Timer(300.0, non_active)
            t.start()
            #self.reset_ptr_rx()
            #self.set_mode(MODE.RXCONT) # Receiver mode
            #time.sleep(10)

    async def tx_enqueue(self, payload):
        await self.queue_tx.put(payload)

    async def lora_tx(self, payload, byte_payload = (__name__!='__main__')):
        while not self.tx_avail:
            await asyncio.sleep(0.001)
        self.tx_avail = False
        self.write_payload([
            0xff, # receiver (0xff for broadcast)
            0x80, # sender
            0x00, # ???
            0x00, # ???
        ] + (list(payload) if byte_payload else to_ascii(payload)))
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

def to_ascii(n):
    assert(type(n) == str)
    return [ord(c) for c in n]

def lora_teardown():
    for lora in loras:
        lora.set_mode(MODE.SLEEP)
        lora.board.teardown()

def lora_setup():
    for lora in loras:
        loop.create_task(lora.start())

###########################################################
loras = []
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
    assert(agc_auto_value == 1)

    #assert(lora.get_agc_auto_on() == 1)
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
        count += 1

def non_active():
    print("Stop sending")
    loop.call_soon_threadsafe(loop.stop)

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
