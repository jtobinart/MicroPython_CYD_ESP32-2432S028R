# CYDc Library
# Tags: Micropython Cheap Yellow Device DIYmall ESP32-2432S028R
# Last Updated: Jan. 27, 2024
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

v1.2
    SD card initialization and mounting have been streamed lined and users no longer need to declare that they want to
    use the SD card when creating an instance of the CYD class.

v1.1
    Double Tap detection implemented. XPT2046 touch switched from SPI to SoftSPI.

v1.0
    This is a higher-level library to control DIYmall's ESP32-2432S028R, also known as the Cheap Yellow Display (CYD).
    
TO DO:
    - Implement continuous touch 
    - Implement DAC pin 26 for the speaker instead of using PWM
    - SD card creates a critical error when using keyboard interrupt
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
    25   Digital   Touch XPT2046              - CLK [Software SPI]
    26   Analog    Speaker                    - !!!Speaker ONLY! Connected to Amp!!!
    27   Digital   Connector CN1              - Can be used as a capacitive touch sensor pin.
    32   Digital   Touch XPT2046              - MOSI [Software SPI]
    33   Digital   Touch XPT2046              - CS [Software SPI]
    34   Analog    LDR Light Sensor           - !!!Input ONLY!!!
    35   Digital   P3 Connector               - !!!Input ONLY w/ NO pull-ups!!!
    36   Digital   Touch XPT2046              - IRQ !!!Input ONLY!!! 
    39   Digital   Touch XPT2046              - MISO !!!Input ONLY!!! [Software SPI]
   
"""

######################################################
#   Import
######################################################
from ili9341 import Display, color565
from xpt2046 import Touch
from machine import Pin, SPI, ADC, PWM, SDCard, SoftSPI
import os
import time

class CYD(object):
    ######################################################
    #   Color Variables
    ######################################################
    BLACK  = color565(  0,   0,   0)
    RED    = color565(255,   0,   0)
    GREEN  = color565(  0, 255,   0)
    CYAN   = color565(  0, 255, 255)
    BLUE   = color565(  0,   0, 255)
    PURPLE = color565(255,   0, 255)
    WHITE  = color565(255, 255, 255)

    ######################################################
    #   Function List
    ######################################################
    '''
        cyd = CYD(rgb_pmw=False, speaker_gain=512)      # Initialize CYD class
        cyd.display.ili9341_function_name()             # Use to access ili9341 functions.
        cyd._touch_handler(x, y)                        # Called when a touch occurs. (INTERNAL USE ONLY)
        cyd.touches()                                   # GETS the last touch coordinates.
        cyd.double_tap(x, y, error_margin = 5)          # Check for double taps.
        cyd.rgb(color)                                          # SETS rgb LED color.
        cyd._remap(value, in_min, in_max, out_min, out_max)     # Converts a value form one scale to another. (INTERNAL USE ONLY)
        cyd.light()                                             # GETS the current light sensor value.
        cyd.button_boot()                               # GETS the current boot button value.
        cyd.backlight(value)                            # SETS backlight brightness.
        cyd.play_tone(freq, duration, gain=0)           # Plays a tone for a given duration.
        cyd.mount_sd()                                  # Mounts SD card         
        cyd.unmount_sd()                                # Unmounts SD card.
        cyd.shutdown()                                  # Safely shutdown CYD device.
    '''
    def __init__(self, rgb_pmw=False, speaker_gain=512):
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
        hspi = SPI(1, baudrate=40000000, sck=Pin(14), mosi=Pin(13))
        self.display = Display(hspi, dc=Pin(2), cs=Pin(15), rst=Pin(0))
        self._x = 0
        self._y = 0
        
        # Backlight
        self.tft_bl = Pin(21, Pin.OUT)
        self.tft_bl.value(1) #Turn on backlight 
        
        # Touch
        self.last_tap = (-1,-1)
        sspi = SoftSPI(baudrate=500000, sck=Pin(25), mosi=Pin(32), miso=Pin(39))
        self._touch = Touch(sspi, cs=Pin(33), int_pin=Pin(36), int_handler=self._touch_handler)
        
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
    
    ######################################################
    #   Touchscreen Press Event
    ###################################################### 
    def _touch_handler(self, x, y):
        '''
        Interrupt Handler
        This function is called each time the screen is touched.
        '''
        # X needs to be flipped
        x = (self.display.width - 1) - x

        self._x = x
        self._y = y

        #print("Touch:", x, y)
    
    def touches(self):
        '''
        Returns last stored touch data.
        
        Return:
            x: x coordinate of finger 1
            y: y coordinate of finger 1
        '''
        x = self._x
        y = self._y
        
        self._x = 0
        self._y = 0
        
        return x, y
    
    def double_tap(self, x, y, error_margin = 5):
        '''
        Returns whether or not a double tap was detected.
        
        Return:
            True: Double-tap detected.
            False: Single tap detected.
        '''
        # Double tap to exit
        if self.last_tap[0] - error_margin <= x and self.last_tap[0] + error_margin >= x:
            if self.last_tap[1] - error_margin <= y and self.last_tap[1] + error_margin >= y:
                self.last_tap = (-1,-1)
                return True
        self.last_tap = (x,y)
        return False
        
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
            if self._sd_ready == False:
                self.sd = SDCard(slot=2)
                self._sd_ready = True
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
        Resets CYD and properly shuts down.
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
