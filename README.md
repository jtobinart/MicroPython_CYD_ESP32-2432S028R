# MicroPython_CYD_ESP32-2432S028R
This is a higher-level library to allows MicroPython users to easily control the ESP32-2432S028R, more commonly known as the Cheap Yellow Display (CYD).

## Dependencies
This library depends on:
* [MicroPython](https://micropython.org/download/ESP32_GENERIC/) - Firmware: v1.22.1 (2024-01-05) .bin
* [rdagger/micropython-ili9341](https://github.com/rdagger/micropython-ili9341/) - ili9341.py, Retrieved: 12/2/23
* [rdagger/micropython-ili9341](https://github.com/rdagger/micropython-ili9341/) - xpt2046.py, Retrieved: 12/2/23

A copy of rdagger's ili9341 and xpt2046 libraries are available in the _resources_ folder.


## Installation
Follow MicroPython's [installation instructions](https://micropython.org/download/ESP32_GENERIC/) to get your CYD board ready. Use your preferred MicroPython IDE (e.g. [Thonny](https://thonny.org/)) to transfer cydr.py, ili9341.py, and xpt2046.py to your CYD board.


## Usage
You can create a new main.py file and use:
```python
from cydr import CYD
cyd = CYD()
```
to access the CYD or you can use one of the example programs provided in the repository.


## License
The repository's code is made available under the terms of the MIT license. Please take a look at license.md for more information.
