# CYDc Library
# Tags: Micropython Cheap Yellow Device DIYmall ESP32-2432S028R
# Last Updated: Dec. 2, 2023
# Author(s): James Tobin
# License: MIT
# https://github.com/jtobinart/MicroPython_CYD_ESP32-2432S028R

import time
from cydr import CYD

cyd = CYD()

duration = 500    # How long to play each note. (in milliseconds)
pause = 1.0       # How long to pause inbetween each note. (in seconds)

# Play a few tones
print("Playing Tone 1")
cyd.play_tone(220, duration)  # A4 Tone
time.sleep(pause)

print("Playing Tone 2")
cyd.play_tone(440, duration)  # C5 Tone
time.sleep(pause)
        
cyd.shutdown()