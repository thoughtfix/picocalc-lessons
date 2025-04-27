# picocalc-lessons
Demo software to help people use MicroPython on PicoCalc



# picocalc-lessons

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache_2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

> A collection of beginner-friendly MicroPython examples for the ClockworkPi PicoCalc.

---

## Table of Contents

- [Overview](#overview)  
- [Goals](#goals)  
- [Examples](#examples)  
- [Prerequisites](#prerequisites)  
- [Contributing](#contributing)  
- [License](#license)  
- [Links](#links)  

---

## Overview

There aren’t many MicroPython examples out there for the PicoCalc yet—most demos are advanced or performance-tuned. This repository aims to help fill that gap by providing **simple**, **overly commented**, and **easy-to-read** scripts that help absolute beginners get comfortable with:

- Drawing to the 320×320 indexed-color display  
- Reading buttons and function keys  
- Implementing basic algorithms (e.g. Game of Life, Snake)  

---

## Goals

- **Beginner-focused**: Extra comments, verbose variable names, and step-by-step logic  
- **MicroPython-only SO FAR**: No external C modules or ports—everything runs on the Pico  
- **Tested in Thonny**: Which is the best way to develop for Pico   
- **Open-source lessons**: Designed for copy-and-paste re-use in your own projects  

---

## Examples

| Script                            | Description                                              |
|-----------------------------------|----------------------------------------------------------|
| `keeb.py`                         | Detect and print raw key codes & ASCII values            |
| `rainbowtest.py`                  | Draw 16 color bands and text on the PicoCalc screen      |
| `calc_calculator.py`              | UNFINISHED:  Scientific calculator                       |
| `life.py`                         | Conway’s Game of Life demo                               |
| `snake.py`                        | Classic Snake with mode options                          |
| …and more to come!        |                                                          |

---

## Prerequisites

1. **ClockworkPi PicoCalc** (with Raspberry Pi Pico 2 or Pico 2 W)  
2. **[MicroPython drivers](https://github.com/zenodante/PicoCalc-micropython-driver)** flashed onto the Pico  
3. **Thonny IDE** (or any MicroPython-friendly editor)  
4. Basic familiarity with Python syntax. 

---

## Contributing

Your pull requests are more than welcome! Whether it’s:
-   A brand-new demo (e.g. Tetris or Mandelbrot maybe?)
-   Better comments or clearer variable names
-   Bug fixes or performance tweaks
I know my code has room for improvement, and hopefully improvements you make will teach future developers down the line. 

## License

All code is licensed under the Apache License 2.0—feel free to re-use, remix, and redistribute. See [LICENSE](LICENSE) for details.

----------

## Links

- [Official PicoCalc page](https://www.clockworkpi.com/picocalc)
-  [ClockworkPi GitHub](https://github.com/clockworkpi)  
-  [ClockworkPi Discord](https://discord.gg/XKGGkPM) 
-  [PicoCalc Micropython Drivers](https://github.com/zenodante/PicoCalc-micropython-driver) by zerodante
-  [MicroPython Official Website](https://micropython.org/)  
-  [MicroPython Documentation](https://docs.micropython.org/)  
-  [Thonny IDE](https://thonny.org/)  

## Additional Resources

- [LaikaSpaceDawg’s PicoCalc MicroPython examples](https://github.com/LaikaSpaceDawg/PicoCalc-micropython)  
- Link to your stuff. (please send a PR)
