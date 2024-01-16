# CYDc Library
# Tags: Micropython Cheap Yellow Device DIYmall ESP32-2432S028R
# Last Updated: Jan. 15, 2024
# Author(s): James Tobin
# License: MIT
# https://github.com/jtobinart/MicroPython_CYD_ESP32-2432S028R

######################################################
#   MIT License
######################################################
'''
Copyright (c) 2023 James Tobin
Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following
conditions:
The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
'''

######################################################
#   Library Information
######################################################
'''
cydr.py:

v1
    This is a higher-level library to control DIYmall's ESP32-2432S028R, also known as the Cheap Yellow Display (CYD).
    
    
    TO DO:
        - Implement DAC pin 26 for the speaker instead of using PWM
        - SD card creates a critical error when using keyboard interrupt. Leave sd_enabled = False, unless using it.
        - Implement easy Bluetooth functions
        - Implement easy Wifi functions
'''

######################################################
#   Pin Reference
######################################################
"""
Pins
     0   Digital   Boot Button
     1   Digital   Connector P1               - TX
     2   Digital   Display                    - TFT_RS / TFT_DC
     3   Digital   Connector P1               - RX
     4   Digital   RGB LED                    - Red
     5   Digital   SD Card                    - SS [VSPI]
     6   Digital   Unpopulated Pad U4: pin 6  - SCK / CLK
     7   Digital   Unpopulated Pad U4: pin 2  - SDO / SD0
     8   Digital   Unpopulated Pad U4: pin 5  - SDI / SD1
     9   Digital   Unpopulated Pad U4: pin 7  - SHD / SD2
    10   Digital   Unpopulated Pad U4: pin 3  - SWP / SD3
    11   Digital   Unpopulated Pad U4: pin 1  - SCS / CMD
    12   Digital   Display                    - TFT_SDO / TFT_MISO [HSPI]
    13   Digital   Display                    - TFT_SDI / TFT_MOSI [HSPI]
    14   Digital   Display                    - TFT_SCK [HSPI]
    15   Digital   Display                    - TFT_CS [HSPI]
    16   Digital   RGB LED                    - Green
    17   Digital   RGB LED                    - Blue
    18   Digital   SD Card                    - SCK [VSPI]
    19   Digital   SD Card                    - MISO [VSPI]
    21   Digital   Display & Connector P3     - TFT_BL (BackLight) / I2C SDA
    22   Digital   Connector P3 & CN1         - I2C SCL
    23   Digital   SD Card                    - MOSI [VSPI]
    25   Digital   Touch XPT2046              - CLK
    26   Analog    Speaker                    - !!!Speaker ONLY! Connected to Amp!!!
    27   Digital   Connector CN1              - Can be used as a capacitive touch sensor pin.
    32   Digital   Touch XPT2046              - MOSI
    33   Digital   Touch XPT2046              - CS
    34   Analog    LDR Light Sensor           - !!!Input ONLY!!!
    35   Digital   P3 Connector               - !!!Input ONLY w/ NO pull-ups!!!
    36   Digital   Touch XPT2046              - IRQ !!!Input ONLY!!!
    39   Digital   Touch XPT2046              - MISO !!!Input ONLY!!!
   
"""


######################################################
#   Import
######################################################
from ili9341 import Display, color565
from xpt2046 import Touch
from machine import idle, Pin, SPI, ADC, PWM, SDCard, DAC
import os
import time

class CYD(object):
    BLACK  = color565(  0,   0,   0)
    RED    = color565(255,   0,   0)
    GREEN  = color565(  0, 255,   0)
    CYAN   = color565(  0, 255, 255)
    BLUE   = color565(  0,   0, 255)
    PURPLE = color565(255,   0, 255)
    WHITE  = color565(255, 255, 255)
    
    def __init__(self, rgb_pmw=False, speaker_gain=512, sd_enabled = False):
        '''
        Initialize CDYc

        Args:
            rgb_pmw (Default = False): Sets RGB LED to static mode. (on/off), if false
                                       Sets RGB LED to dynamic mode. (16.5+ million color combination), if true
                                       Warning: RGB LED never completely turns off in dynamic mode.
            
            speaker_gain (Default = 512): Sets speaker's volume. The full gain range is 0 - 1023.

            sd_enabled (Default = False): Initializes SD Card reader, user still needs to run mount_sd() to access SD card.
        '''
        # Display
        spi1 = SPI(1, baudrate=40000000, sck=Pin(14), mosi=Pin(13))
        self.display = Display(spi1, dc=Pin(2), cs=Pin(15), rst=Pin(0))
        self._x = 0
        self._y = 0
        
        # Backlight
        self.tft_bl = Pin(21, Pin.OUT)
        self.tft_bl.value(1) #Turn on backlight 
        
        # Touch
        spi2 = SPI(2, baudrate=1000000, sck=Pin(25), mosi=Pin(32), miso=Pin(39))
        self._touch = Touch(spi2, cs=Pin(33), int_pin=Pin(36), int_handler=self.touched)
        
        # Boot Button
        self._button_boot = Pin(0, Pin.IN)
        
        # LDR: Light Sensor (Measures Darkness)
        self._ldr = ADC(34)
        
        # RGB LED
        self._rgb_pmw = rgb_pmw
        if self._rgb_pmw == False:
            self.RGBr = Pin(4, Pin.OUT, value=1)     # Red
            self.RGBg = Pin(16, Pin.OUT, value=1)    # Green
            self.RGBb = Pin(17, Pin.OUT, value=1)    # Blue
        else:
            self.RGBr = PWM(Pin(4), freq=200, duty=1023)     # Red
            self.RGBg = PWM(Pin(16), freq=200, duty=1023)    # Green
            self.RGBb = PWM(Pin(17), freq=200, duty=1023)    # Blue
            print("RGB PMW Ready")
        
        # Speaker
        self._speaker_pin = Pin(26, Pin.OUT)
        self.speaker_gain = int(min(max(speaker_gain, 0),1023))     # Min 0, Max 1023
        self.speaker_pwm = PWM(self._speaker_pin, freq=440, duty=0)
            
        # SD Card
        self._sd_ready = False
        self._sd_mounted = False
        if sd_enabled == True:
            try:
                self.sd = SDCard(slot=2)
                self._sd_ready = True
                print("SD card ready to mount.")
            except:
                print("Failed to setup SD Card.") 
    
    ######################################################
    #   Touchscreen Press Event
    ###################################################### 
    def touched(self, x, y):
        '''
        Interrupt Handler
        This function is called each time the screen is touched.
        '''
        # Y needs to be flipped
        y = (self.display.height - 1) - y

        self._x = x
        self._y = y

        print("Touch:", x, y)
    
    def touches():
        '''
        Returns last stored touch data.
        
        Return:
            x: x coordinate of finger 1
            y: y coordinate of finger 1
        '''
        return self._x, self._y
    
    ######################################################
    #   RGB LED
    ###################################################### 
    def rgb(self, color):
        '''
        Set RGB LED color.
        
        Args:
            color: Array containing three int values (r,g,b).
                    if rgb_pmw == False, then static mode is activated.
                        r (0 or 1): Red brightness.
                        g (0 or 1): Green brightness.
                        b (0 or 1): Blue brightness.
                    if rgb_pmw == True, then dynamic mode is activated.
                        r (0-255): Red brightness.
                        g (0-255): Green brightness.
                        b (0-255): Blue brightness.
        '''
        r, g, b = color
        if self._rgb_pmw == False:
            self.RGBr.value(1 if min(max(r, 0),1) == 0 else 0)
            self.RGBg.value(1 if min(max(g, 0),1) == 0 else 0)
            self.RGBb.value(1 if min(max(b, 0),1) == 0 else 0)
        else:
            self.RGBr.duty(int(min(max(self._remap(r,0,255,1023,0), 0),1023)))
            self.RGBg.duty(int(min(max(self._remap(g,0,255,1023,0), 0),1023)))
            self.RGBb.duty(int(min(max(self._remap(b,0,255,1023,0), 0),1023)))
    
    def _remap(self, value, in_min, in_max, out_min, out_max):
        '''
        Internal function for remapping values from one scale to a second.
        '''
        in_span = in_max - in_min
        out_span = out_max - out_min
        scale = out_span / in_span
        return out_min + (value - in_min) * scale
    
    ######################################################
    #   Light Sensor
    ###################################################### 
    def light(self):
        '''
        Light Sensor (Measures darkness)
        
        Return: a value from 0.0 to 1.0
        '''
        return self._ldr.read_u16()/65535
    
    ######################################################
    #   Button
    ###################################################### 
    def button_boot(self):
        '''
        Gets the Boot button's current state
        '''
        return self._button_boot.value
    
    ######################################################
    #   Backlight
    ###################################################### 
    def backlight(self, val):
        '''
        Sets TFT Backlight Off/On
        
        Arg:
            val: 0 or 1 (0 = off/ 1 = on)
        '''
        self.tft_bl.value(min(max(val, 0),1))
    
    ######################################################
    #   Speaker
    ###################################################### 
    def play_tone(self, freq, duration, gain=0):
        '''
        Plays a tone (Optional speaker must be attached!)
        
        Args:
            freq: Frequency of the tone.
            duration: How long does the tone play for.
            gain: volume
        '''
        self.speaker_pwm.freq(freq)
        if gain == 0:
            gain = self.speaker_gain
        self.speaker_pwm.duty(gain)             # Turn on speaker by resetting speaker gain
        time.sleep_ms(duration)
        self.speaker_pwm.duty(0)                # Turn off speaker by resetting gain to zero
    
    ######################################################
    #   SD Card
    ###################################################### 
    def mount_sd(self):
        '''
        Mounts SD Card
        '''
        try:
            if self._sd_ready == True:
                os.mount(self.sd, '/sd')  # mount
                self._sd_mounted = True
                print("SD card mounted. Do not remove!")
        except:
            print("Failed to mount SD card")
    
    def unmount_sd(self):
        '''
        Unmounts SD Card
        '''
        try:
            if self._sd_mounted == True:
                os.unmount('/sd')  # mount
                self._sd_mounted = False
                print("SD card unmounted. Safe to remove SD card!")
        except:
            print("Failed to unmount SD card")
    
    ######################################################
    #   Shutdown
    ###################################################### 
    def shutdown(self):
        '''
        Resets CYD and properly shutsdown.
        '''
        self.display.fill_rectangle(0, 0, self.display.width-1, self.display.height-1, self.BLACK)
        self.display.draw_rectangle(2, 2, self.display.width-5, self.display.height-5, self.RED)
        self.display.draw_text8x8(self.display.width // 2 - 52, self.display.height // 2 - 4, "Shutting Down", self.WHITE, background=self.BLACK)
        time.sleep(2.0)
        self.unmount_sd()
        self.speaker_pwm.deinit()
        if self._rgb_pmw == False:
            self.RGBr.value(1)
            self.RGBg.value(1)
            self.RGBb.value(1)
        else:
            self.rgb(0,0,0)
        self.tft_bl.value(0)
        self.display.cleanup()
        print("========== Goodbye ==========")
