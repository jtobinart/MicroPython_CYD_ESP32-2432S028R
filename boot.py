# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

from machine import Pin

print("Booting...")
RGB = Pin(21, Pin.OUT)    # Set RGB LED pin
RGB.value(0)              # Turn off RGB LED