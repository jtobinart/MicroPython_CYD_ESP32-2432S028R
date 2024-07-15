# CYDc Simple WIFI Demo
# Tags: Micropython Smaller Cheap Yellow Device Capacitive Touch cst820 DIYmall ESP32-2432S024C 
# Last Updated: June 14, 2024
# Author(s): James Tobin
# License: MIT
# https://github.com/jtobinart/Micropython_CYDc_ESP32-2432S024C

from cydr import CYD
import time
import urequests

# Create an instance of CYD with WIFI support
ssid = "change_me"     # The name of the WIFI network you want to connect to.
password = "change_me" # The password of the WIFI network you want to connect to.

cyd = CYD(wifi_ssid=ssid, wifi_password=password)
url = "http://api.coindesk.com/v1/bpi/currentprice.json"
#url = "http://api.open-notify.org/astros.json"
#url = "http://ip-api.com/json/"

end_time = 0

while cyd.wifi_isconnected():
    x, y = cyd.touches()    # Get recent taps x, y
    
    if time.ticks_ms() > end_time:
        r = urequests.get(url).json()
        print(r['bpi']['USD']['rate_float'])
        text = "B" + str(r['bpi']['USD']['rate_float'])
        
        # draw text
        cyd.display.draw_text8x8(cyd.display.width // 2 - 40, cyd.display.height // 2 - 4, text, cyd.WHITE, background=cyd.RED)
        
        # reset end_time
        # We don't want to overburden the server and the CYD with requests so we request updates every 3 minutes.
        end_time = time.ticks_ms() + 180000   # 60000ms = 1 minute
    
    # Check that there ar new touch points (Default values are x = 0, y = 0)
    if x == 0 and y == 0:
        continue
    
    # Double tap to exit
    if cyd.double_tap(x,y):
        cyd.shutdown()

