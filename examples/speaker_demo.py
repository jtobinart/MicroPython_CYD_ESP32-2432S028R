# CYDc Library
# Tags: Micropython Cheap Yellow Device DIYmall ESP32-2432S028R
# Last Updated: Jan. 15, 2024
# Author(s): James Tobin
# License: MIT
# https://github.com/jtobinart/MicroPython_CYD_ESP32-2432S028R

import time
from cydr import CYD

cyd = CYD()

cyd.display.fill_rectangle(0, 0, cyd.display.width-1, cyd.display.height-1, cyd.BLUE)


duration = 500    # How long to play each note. (in milliseconds)
pause = 2.0       # How long to pause in between each tone. (in seconds)

# Play tone 1
print("Playing Tone 1")
cyd.display.draw_text8x8(cyd.display.width // 2 - 56, cyd.display.height // 2 - 4, "Playing Tone 1", cyd.WHITE, background=cyd.BLUE)

cyd.play_tone(220, duration)  # A4 Tone
time.sleep(pause)

# Play tone 2
print("Playing Tone 2")
cyd.display.draw_text8x8(cyd.display.width // 2 - 56, cyd.display.height // 2 - 4, "Playing Tone 2", cyd.WHITE, background=cyd.BLUE)

cyd.play_tone(440, duration)  # C5 Tone
time.sleep(pause)
        
cyd.shutdown()
