import struct
import sys
import time
from SX127x.constants import *
from lora import LoRa
from board_config import BOARD #2 as BOARD

BOARD.setup()
BOARD.reset()
#parser = LoRaArgumentParser("Lora tester")

BOOT_MSG_STRUCT = struct.Struct('<HHbHbbbbfbHHbbbHbHbbHHHH10s')

class mylora(LoRa):
    def __init__(self, board, verbose=False):
        super(mylora, self).__init__(board,verbose=verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
        self.var=0

    def on_rx_done(self):
        BOARD.led_on()
        #print("\nRxDone")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        print("Receive: {} bytes".format(len(payload)))
        BOARD.led_off()
        if payload[4] == 4 and len(payload) == BOOT_MSG_STRUCT.size:
            (src,dst,pkttype,firmware,model,reset,
            radio_device_address,
            radio_gateway_address,
            radio_freq,
            radio_tx_power,
            collect_interval_day,
            collect_interval_night,
            day_start_hour,
            day_end_hour,
            time_zone,
            advertise_interval,
            use_ack,
            ack_timeout,
            long_range,
            tx_repeat,
            gps_max_wait_for_fix,
            next_collect_no_fix,
            total_slots,
            slot_interval,
            prog_file_name) = BOOT_MSG_STRUCT.unpack(bytes(payload))
            print(f"Device boot detected from {src} to {dst}")
            print(f" * Firmware version: {firmware}")
            print(f" * Device address: {radio_device_address}")
            print(f" * Gateway address: {radio_gateway_address}")
            print(f" * Radio frequency: {radio_freq}")
            print(f" * Radio TX power: {radio_tx_power}")

        #time.sleep(2) # Wait for the client be ready
        #print ("Send: ACK")
        #self.write_payload([255, 255, 0, 0, 65, 67, 75, 0]) # Send ACK
        #self.set_mode(MODE.TX)
        #self.var=1

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

    def start(self):          
        while True:
            #while (self.var==0):
            #    print ("Send: INF")
            #    self.write_payload([255, 255, 0, 0, 73, 78, 70, 0]) # Send INF
            #    self.set_mode(MODE.TX)
            #    time.sleep(3) # there must be a better solution but sleep() works
            #    self.reset_ptr_rx()
            #    self.set_mode(MODE.RXCONT) # Receiver mode
            #
            #    start_time = time.time()
            #    while (time.time() - start_time < 10): # wait until receive data or 10s
            #        pass;
            #
            #self.var=0
            self.reset_ptr_rx()
            self.set_mode(MODE.RXCONT) # Receiver mode
            time.sleep(10)

lora = mylora(BOARD, verbose=True)
#args = parser.parse_args(lora) # configs in LoRaArgumentParser.py

#     Slow+long range  Bw = 125 kHz, Cr = 4/8, Sf = 4096chips/symbol, CRC on. 13 dBm
lora.set_pa_config(pa_select=1, max_power=21, output_power=15)
lora.set_bw(BW.BW125)
lora.set_freq(434.0)
lora.set_coding_rate(CODING_RATE.CR4_8)
lora.set_spreading_factor(12)
lora.set_rx_crc(True)
#lora.set_lna_gain(GAIN.G1)
#lora.set_implicit_header_mode(False)
lora.set_low_data_rate_optim(True)

#  Medium Range  Defaults after init are 434.0MHz, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on 13 dBm
#lora.set_pa_config(pa_select=1)


assert(lora.get_agc_auto_on() == 1)

try:
    print("START")
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    print("Exit")
    sys.stderr.write("KeyboardInterrupt\n")
finally:
    sys.stdout.flush()
    print("Exit")
    lora.set_mode(MODE.SLEEP)
    BOARD.teardown()

