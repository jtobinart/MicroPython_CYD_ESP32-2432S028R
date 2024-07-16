# CYDr Advance WIFI Demo
# Tags: Micropython Cheap Yellow Device DIYmall ESP32-2432S028R
# Last Updated: June 15, 2024
# Author(s): James Tobin
# License: MIT
# https://github.com/jtobinart/MicroPython_CYD_ESP32-2432S028R

from cydr import CYD
import time
import network
import urequests

# Create an instance of CYD with WIFI support
ssid = "change_me"         # The name of the WIFI network you want to connect to.
password = "change_me" # The password of the WIFI network you want to connect to.

cyd = CYD()

# Create a WIFI interface.
wifi = network.WLAN(network.STA_IF)
wifi.active(True)

text = "You are in:"
cyd.display.draw_text8x8(cyd.display.width // 2 - int((len(text)*8)/2), cyd.display.height // 2 - 16, text, cyd.WHITE)

url = "http://ip-api.com/json/"

end_time = 0

while not wifi.isconnected():

    #Attempt to connect to WIFI network
    print("Connecting to network...")
    wifi.connect(ssid, password)
    time.sleep(0.1)
    
while wifi.isconnected():
    x, y = cyd.touches()    # Get recent taps x, y
    
    if time.ticks_ms() > end_time:
        r = urequests.get(url).json()
        #print(r)    # Uncomment to print all data.
        text = str(r['city'])
        
        # draw text
        cyd.display.draw_text8x8(cyd.display.width // 2 - int((len(text)*8)/2), cyd.display.height // 2 - 4, text, cyd.WHITE)
        
        # reset end_time
        # We don't want to overburden the server and the CYD with requests so we request updates every 3 minutes.
        # This method also allows the other functions like the touch function to work in the background.
        end_time = time.ticks_ms() + 180000   # 60000ms = 1 minute
    
    # Check that there ar new touch points (Default values are x = 0, y = 0)
    if x == 0 and y == 0:
        continue
    
    # Double tap to exit
    if cyd.double_tap(x,y):
        cyd.shutdown()
