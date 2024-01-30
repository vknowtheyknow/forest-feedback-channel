""" Defines the BOARD class that contains the board pin mappings and RF module HF/LF info. """
# -*- coding: utf-8 -*-

# Copyright 2015-2018 Mayer Analytics Ltd. and Rui Silva
#
# This file is part of rpsreal/pySX127x.
#
# pySX127x is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pySX127x is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You can be released from the requirements of the license by obtaining a commercial license. Such a license is
# mandatory as soon as you develop commercial activities involving pySX127x without disclosing the source code of your
# own applications, or shipping pySX127x with a closed source product.
#
# You should have received a copy of the GNU General Public License along with pySX127.  If not, see
# <http://www.gnu.org/licenses/>.


import RPi.GPIO as GPIO
import spidev

import time


class BOARD:
    """ Board initialisation/teardown and pin configuration is kept here.
        Also, information about the RF module is kept here.
        This is the Raspberry Pi board with one LED and a Ra-02 Lora.
    """
    # Note that the BCOM numbering for the GPIOs is used.
    DIO0 = 24   # RaspPi GPIO 24
    DIO1 = 6    # RaspPi GPIO  6
    RST  = 17   # RaspPi GPIO 17
    LED  = 4

    # The spi object is kept here
    spi = None
    SPI_BUS=0
    SPI_CS=0
    
    # tell pySX127x here whether the attached RF module uses low-band (RF*_LF pins) or high-band (RF*_HF pins).
    # low band (called band 1&2) are 137-175 and 410-525
    # high band (called band 3) is 862-1020
    low_band = True

    @classmethod
    def setup(cls):
        """ Configure the Raspberry GPIOs
        :rtype : None
        """
        GPIO.setmode(GPIO.BCM)
        # LED
        GPIO.setup(cls.LED, GPIO.OUT)
        GPIO.setup(cls.RST, GPIO.OUT)
        GPIO.output(cls.LED, 1)
        GPIO.output(cls.RST, 1)
        # switch
        #GPIO.setup(cls.SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
        # DIOx
        for gpio_pin in [cls.DIO0, cls.DIO1]:
            GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # blink 2 times to signal the board is set up
        cls.blink(.1, 2)

    @classmethod
    def teardown(cls):
        """ Cleanup GPIO and SpiDev """
        GPIO.cleanup()
        cls.spi.close()

    @classmethod
    def SpiDev(cls):
        """ Init and return the SpiDev object
        :return: SpiDev object
        :param spi_bus: The RPi SPI bus to use: 0 or 1
        :param spi_cs: The RPi SPI chip select to use: 0 or 1
        :rtype: SpiDev
        """
        spi_bus=cls.SPI_BUS
        spi_cs=cls.SPI_CS
        cls.spi = spidev.SpiDev()
        cls.spi.open(spi_bus, spi_cs)
        cls.spi.max_speed_hz = 5000000    # SX127x can go up to 10MHz, pick half that to be safe
        cls.spi.no_cs = True
        return cls.spi

    @classmethod
    def add_event_detect(cls, dio_number, callback):
        """ Wraps around the GPIO.add_event_detect function
        :param dio_number: DIO pin 0...5
        :param callback: The function to call when the DIO triggers an IRQ.
        :return: None
        """
        GPIO.add_event_detect(dio_number, GPIO.RISING, callback=callback)

    @classmethod
    def add_events(cls, cb_dio0, cb_dio1, cb_dio2, cb_dio3, cb_dio4, cb_dio5, switch_cb=None):
        cls.add_event_detect(cls.DIO0, callback=cb_dio0)
        cls.add_event_detect(cls.DIO1, callback=cb_dio1)
        # the modtronix inAir9B does not expose DIO4 and DIO5
        if switch_cb is not None:
            GPIO.add_event_detect(cls.SWITCH, GPIO.RISING, callback=switch_cb, bouncetime=300)

    @classmethod
    def led_on(cls):
        """ Switch the proto shields LED
        :param value: 0/1 for off/on. Default is 1.
        :return: value
        :rtype : int
        """
        GPIO.output(cls.LED, 0)
        return 1

    @classmethod
    def led_off(cls):
        """ Switch LED off
        :return: 0
        """
        if cls.LED:
            GPIO.output(cls.LED, 1)
        return 0
    
    @classmethod
    def reset(cls):
        """ manual reset
        :return: 0
        """
        GPIO.output(cls.RST, 0)
        time.sleep(.01)
        GPIO.output(cls.RST, 1)
        time.sleep(.01)
        return 0

    @classmethod
    def blink(cls, time_sec, n_blink):
        if n_blink == 0:
            return
        cls.led_on()
        for i in range(n_blink):
            time.sleep(time_sec)
            cls.led_off()
            time.sleep(time_sec)
            cls.led_on()
        cls.led_off()
        

#################################################
class BOARD2:
    """ Board initialisation/teardown and pin configuration is kept here.
        Also, information about the RF module is kept here.
        This is the Raspberry Pi board with one LED and a Ra-02 Lora.
    """
    # Note that the BCOM numbering for the GPIOs is used.
    DIO0 = 12   # RaspPi GPIO 25
    DIO1 = 19   # RaspPi GPIO 13
    RST  = 27   # RaspPi GPIO 23
    LED  = None

    # The spi object is kept here
    spi = None
    SPI_BUS=0
    SPI_CS=20
    
    # tell pySX127x here whether the attached RF module uses low-band (RF*_LF pins) or high-band (RF*_HF pins).
    # low band (called band 1&2) are 137-175 and 410-525
    # high band (called band 3) is 862-1020
    low_band = True

    @classmethod
    def setup(cls):
        """ Configure the Raspberry GPIOs
        :rtype : None
        """
        GPIO.setmode(GPIO.BCM)
        # LED
        if cls.LED:
            GPIO.setup(cls.LED, GPIO.OUT)
            GPIO.output(cls.LED, 1)
        GPIO.setup(cls.RST, GPIO.OUT)
        GPIO.output(cls.RST, 1)
        # switch
        #GPIO.setup(cls.SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
        # DIOx
        for gpio_pin in [cls.DIO0, cls.DIO1]:
            GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # blink 2 times to signal the board is set up
        cls.blink(.1, 2)

    @classmethod
    def teardown(cls):
        """ Cleanup GPIO and SpiDev """
        GPIO.cleanup()
        cls.spi.close()

    @classmethod
    def SpiDev(cls):
        """ Init and return the SpiDev object
        :return: SpiDev object
        :param spi_bus: The RPi SPI bus to use: 0 or 1
        :param spi_cs: The RPi SPI chip select to use: 0 or 1
        :rtype: SpiDev
        """
        spi_bus=cls.SPI_BUS
        spi_cs=cls.SPI_CS
        cls.spi = spidev.SpiDev()
        cls.spi.open(spi_bus, spi_cs)
        cls.spi.max_speed_hz = 5000000    # SX127x can go up to 10MHz, pick half that to be safe
        return cls.spi

    @classmethod
    def add_event_detect(cls, dio_number, callback):
        """ Wraps around the GPIO.add_event_detect function
        :param dio_number: DIO pin 0...5
        :param callback: The function to call when the DIO triggers an IRQ.
        :return: None
        """
        GPIO.add_event_detect(dio_number, GPIO.RISING, callback=callback)

    @classmethod
    def add_events(cls, cb_dio0, cb_dio1, cb_dio2, cb_dio3, cb_dio4, cb_dio5, switch_cb=None):
        cls.add_event_detect(cls.DIO0, callback=cb_dio0)
        cls.add_event_detect(cls.DIO1, callback=cb_dio1)
        # the modtronix inAir9B does not expose DIO4 and DIO5
        if switch_cb is not None:
            GPIO.add_event_detect(cls.SWITCH, GPIO.RISING, callback=switch_cb, bouncetime=300)

    @classmethod
    def led_on(cls):
        """ Switch the proto shields LED
        :param value: 0/1 for off/on. Default is 1.
        :return: value
        :rtype : int
        """
        if cls.LED:
            GPIO.output(cls.LED, 0)
        return 1

    @classmethod
    def led_off(cls):
        """ Switch LED off
        :return: 0
        """
        if cls.LED:
            GPIO.output(cls.LED, 1)
        return 0
    
    @classmethod
    def reset(cls):
        """ manual reset
        :return: 0
        """
        GPIO.output(cls.RST, 0)
        time.sleep(.01)
        GPIO.output(cls.RST, 1)
        time.sleep(.01)
        return 0

    @classmethod
    def blink(cls, time_sec, n_blink):
        pass
        

