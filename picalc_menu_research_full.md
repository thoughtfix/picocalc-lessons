# ClockworkPi PicoCalc MicroPython Technical Study
Written by LLMs, with prompts and research by code@danielgentleman.com  
Version 0.2b (draft, checking for errors)  
April 29, 2025  

## Goals

- The Clockwork Pi PicoCalc boot process with MicroPython.
- How display and keyboard initialization happens, and how vtterminal interacts with it.
- Constraints and available modules in the PicoCalc-specific MicroPython environment.
- Issues and best practices around running scripts dynamically from both the local REPL and via Thonny.
- How to design a Python-first, text-based dynamic menu system that doesn't reinitialize hardware improperly, and that can select and run programs while keeping Thonny REPL operational.



## 1. Boot Procedure and Hardware Initialization

**MicroPython Boot Sequence:** The PicoCalc runs a custom MicroPython firmware that executes `boot.py` and then `main.py` on startup, similar to standard MicroPython. On the PicoCalc, `boot.py` is used to perform early setup (e.g. allocating large memory for Eigenmath in specialized builds ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=Using%20eigenmath))) and to initialize hardware drivers, while `main.py` typically launches the user interface or REPL. In the provided firmware, `boot.py` sets up the device’s screen and keyboard drivers so that by the time `main.py` runs, the hardware is ready for use ([PicoCalc-micropython-driver/pico_files/main.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/main.py#:~:text=os)). If the device is powered via its normal port (USB-C or battery), `boot.py` and `main.py` will run automatically. (Notably, if powered via the Pico’s BOOTSEL USB port, `main.py` may be skipped to allow a serial connection for development ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=Image%3A%20%3Awarning%3A%20Notes%20%26%20Caveats%3A)).)

**Display Initialization:** The PicoCalc uses an SPI-connected 480x320 ILI9488 LCD (the firmware currently uses a 320×320 region in 16-color mode ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=Image%3A%20%3Aframed_picture%3A%20Framebuffer%20%26%20Graphics%3A))). The custom display driver is packaged as a MicroPython C module (`picocalcdisplay`), with a Python wrapper class `PicoDisplay`. During boot, the firmware creates a `PicoDisplay` instance with the desired resolution and color depth (by default, 4-bit color for 16-color palette) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=class%20PicoDisplay%28framebuf)) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=super%28%29)). This allocates a frame buffer in RAM and initializes the LCD via `picocalcdisplay.init(...)` ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=super%28%29)). The driver enables **auto-refresh on the second core** of the RP2040, meaning the screen buffer is continuously pushed to the display in the background ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=%2A%20C%20module%20supports%20high,for%20a%20smoother%20REPL%20experience)). This offloads display updates to core 1 for smoother performance, allowing the REPL or user code to run on core 0 without stalling the display. By default the screen is memory-mapped as a MicroPython `framebuf` (16-color) so graphics primitives like pixels, lines, text, etc., can be drawn. The display starts in text/terminal mode (showing the MicroPython banner/REPL) once initialized.

**VT100 Terminal Setup:** Immediately after initializing the frame buffer and display, the firmware instantiates a **VT100 terminal emulator** (provided by the `vtterminal` C module, accessed via a Python module `vt`). The code creates a terminal object with `vt.vt(display, keyboard, sd=sd)` passing in the display and keyboard objects (and SD card, if mounted) ([PicoCalc-micropython-driver/pico_files/main.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/main.py#:~:text=pc_display%20%3D%20PicoDisplay%28320%2C320%29)). This VT100 emulator integrates with MicroPython’s I/O system: the firmware calls `os.dupterm(pc_terminal)` to duplicate the MicroPython REPL on this terminal ([PicoCalc-micropython-driver/pico_files/main.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/main.py#:~:text=os)). As a result, the on-board display and keyboard become the “console” for MicroPython. The VT100 module clears the screen and sets up a 40×(?)-line text console buffer on the LCD. Any output printed by MicroPython (REPL prompts, print statements, errors) will be rendered as text on the LCD, and key presses on the PicoCalc’s keyboard feed into the REPL input ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=Now%20with%20keyword%20highlighting%20support)). After this point, the device operates like a self-contained terminal. (Under the hood, the VT100 driver draws characters into the frame buffer and the display driver’s core1 task continuously refreshes the LCD, giving the appearance of a live console.)

**Keyboard Initialization:** The PicoCalc’s QWERTY keyboard is provided via an onboard STM32 co-processor acting as an I²C device (address `0x1F`) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=def%20__init__)) ([PicoCalc | ClockworkPi](https://www.clockworkpi.com/picocalc#:~:text=ClockworkPi%20v2,development%20and%20save%20IO%20resources)). Early in `main.py` (or `boot.py` in newer versions), a `PicoKeyboard` object is created to initialize this device ([PicoCalc-micropython-driver/pico_files/main.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/main.py#:~:text=pc_display%20%3D%20PicoDisplay%28320%2C320%29)). The keyboard driver sets up I²C1 on specific pins (by default GP7=SCL, GP6=SDA in the custom firmware) and resets the keyboard controller ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=def%20__init__)) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=def%20reset)). Once initialized, the keyboard begins sending key events to an internal FIFO, which the driver can read. The custom driver maps the raw key matrix codes to ANSI key codes or control sequences. For example, arrow keys are reported with codes 0xB4–0xB7 which the driver will translate into VT100 escape sequences (`ESC [ A/B/C/D`) when feeding the terminal ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=if%20key%20%3D%3D%200xB4%3A)) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=self.hardwarekeyBuf.extend%28b%27)). The keyboard driver also exposes methods to check battery level and control the backlight (since the same STM32 handles power management) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=def%20battery)) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=def%20setBacklight_keyboard)). The keyboard is **made available as soon as `PicoKeyboard()` is called**. In the REPL context, the VT terminal will start reading from the keyboard driver immediately after initialization, so by the time the user sees the first prompt, key presses are being handled. In summary, `boot.py/main.py` brings up the LCD and keyboard, then hands off control to the VT100 console, leaving MicroPython ready to accept input from the device’s own keyboard.

**State for User Programs:** After this boot procedure, the **display is in use by the VT100 console** (in text mode with a 16-color palette) and the **keyboard is captured by the VT** for REPL input. This means any user program starts with an already-initialized display (`pc_display`) and keyboard (`pc_keyboard`) object available (often as globals in the environment). It’s important to note that the display is continuously being refreshed via core1. If a user program wants to draw to the screen, it can reuse the existing `pc_display` frame buffer (e.g. using MicroPython `framebuf` methods or the `picocalcdisplay` API) and then call `pc_display.show()` to push an update ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=def%20text)) – though often, for text output, simply printing suffices because the VT100 will handle rendering text. **Re-initializing the display or creating a second display object is not recommended**, as the VT100/refresh thread is already active. Similarly, the keyboard object is already polling I²C – user code can read from it if needed (for example, via `pc_keyboard.keyEvent()`), but creating another `PicoKeyboard` instance on the same I²C bus could conflict. In essence, the firmware’s startup leaves a **pre-configured environment** for other code: a 320x320 frame buffer with auto-refresh, and a keyboard input stream feeding the REPL.

## 2. REPL Behavior (On-Device vs. Serial)

**On-Device REPL:** Once booted, the PicoCalc drops into the MicroPython REPL which is displayed on the device’s own screen (via the VT100 emulator) and accessible through the PicoCalc’s keyboard. Users see the familiar `>>>` prompt on the LCD and can type Python commands using the built-in keyboard. The VT100 terminal handles special keys for command editing just as a PC terminal would – for example, arrow keys move through history (the firmware translates them to `ESC[A/B` sequences and the MicroPython REPL interprets those) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=if%20key%20%3D%3D%200xB4%3A)) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=self.hardwarekeyBuf.extend%28b%27)). From the user’s perspective, the PicoCalc behaves like a tiny computer running a MicroPython shell. This REPL is fully functional: you can import modules, define functions, and so on, and the output is rendered on the screen. Because of the `os.dupterm` setup, the **USB serial is no longer the primary console** – the REPL I/O is bound to the vt100 terminal (`pc_terminal`) ([PicoCalc-micropython-driver/pico_files/main.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/main.py#:~:text=os)). The keyboard driver works seamlessly with this REPL; for instance, pressing `Ctrl+U` on the device triggers a screen capture feature implemented by the vt module (dumping the frame buffer to the SD card) ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=,for%20a%20smoother%20REPL%20experience)). In short, the on-device REPL is interactive and uses the PicoCalc’s display/keyboard exclusively.

**Serial REPL via Thonny (USB):** It is still possible to access the MicroPython REPL over USB, but the behavior depends on how the device is powered and configured. **By design, if the PicoCalc is powered via the RP2040’s micro-USB (BOOTSEL) port and connected to a PC, the firmware will favor the USB serial REPL instead of auto-launching the on-device interface** ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=Image%3A%20%3Awarning%3A%20Notes%20%26%20Caveats%3A)). In practice, users have noted that when powering the board from the micro-USB, `main.py` may not run automatically ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=Image%3A%20%3Awarning%3A%20Notes%20%26%20Caveats%3A)). This is likely intentional (or a side-effect of MicroPython’s USB behavior) to allow developers to connect with Thonny or another IDE without the device taking over the REPL. In this scenario, MicroPython will present the REPL on the USB serial as usual, and you can type commands from your PC. The device’s screen may remain blank (or showing a boot message) until you manually initialize it. You can still use the device’s keyboard in this mode by explicitly importing and using the driver, but by default the input comes from USB. If the PicoCalc is instead powered by battery or the USB-C port (not data-enabled for the RP2040), then `main.py` runs and the REPL is captured by the device itself, and the USB serial will either be idle or unavailable for commands ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=,you%20can%E2%80%99t%20connect%20via%20Thonny)). 

**Switching Between REPLs:** In the firmware’s current form, once the VT100 console is active, the USB serial is essentially a secondary interface. MicroPython can support multiple REPLs (there is a `dupterm` slot 0 and 1), but the implementation here likely uses the VT terminal as the primary. In practice this means when the on-device REPL is running, connecting Thonny might not show the prompt or output. To get a serial prompt, one approach is to **boot the device with the micro-USB connected (to skip the on-device REPL)**, or otherwise interrupt the running interface. Pressing **Ctrl+C on the PC** may send an interrupt – in many MicroPython builds, a `KeyboardInterrupt` can be raised even if that interface isn’t the active dupterm (the USB often can inject an interrupt). Users have reported that if the device is already in VT REPL mode, Thonny cannot connect (because the USB is taken over by the filesystem interface or simply no output) ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=,you%20can%E2%80%99t%20connect%20via%20Thonny)). As a workaround during development, you can power via micro-USB to get a standard REPL, or physically reset the board and quickly connect with Thonny before `main.py` runs. The firmware is still evolving in this regard. 

**Local vs Remote Execution Differences:** A quirk observed is that programs may behave differently when run **locally on the device vs. remotely from Thonny**. This stems from differences in environment and execution method:

- *Execution environment:* When running code **on the device’s REPL**, you already have the PicoCalc hardware environment set up (display on, vt100 active, etc.). For example, printing goes to the LCD, and `input()` will read from the PicoCalc keyboard. In contrast, when you run code via **Thonny**, often Thonny will send the file over and execute it, which may happen in an environment where the display and keyboard aren’t initialized (if `main.py` was skipped). In that case, calls that assume an existing `pc_display` or `pc_terminal` will fail or do nothing. You might need to manually import and initialize the `picocalc` drivers in scripts run from Thonny. In short, the **on-device run has all the drivers pre-initialized**, whereas a remote run might be closer to a vanilla MicroPython environment unless you explicitly set it up.

- *Import vs direct execution:* On the device, users commonly run a program by typing `import myprogram` at the REPL. This has a key implication: in MicroPython (as in Python), doing an `import` will execute the module code **only once** and will not automatically re-run it on subsequent imports (unless using `importlib.reload`). If the module is written with a `def main(): ...` and guarded by `if __name__ == "__main__": main()`, then importing it will **not** call `main()` (because the module’s `__name__` will not be `"__main__"`). This can lead to confusion where importing a script on-device appears to do nothing if all functionality is inside that `main()` function. However, when running the same script from Thonny, Thonny typically executes the file in a __main__ context (as a script) rather than importing, so the code runs fully. This explains why a program with its own `main()` might behave differently: via Thonny it runs, but via on-device import it doesn’t start automatically. The PicoCalc firmware provides a helper `run()` function to address this: for example, `from picocalc_system import run; run("my_test.py")` will explicitly execute a file as a script ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=gary_m%20%20April%2017%2C%202025%2C,11%3A22pm%20%2012)) ([PicoCalc-micropython-driver/pico_files/modules/picocalc_system.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc_system.py#:~:text=try%3A)), ensuring it runs the same way in both scenarios.

- *REPL differences:* Another difference is in **input/output handling**. A program that, say, uses `input()` to pause for user input will work on-device (waiting for keys on the Pico keyboard via the vt100) just as on a normal PC terminal. If the same program is run under Thonny, the `input()` will be waiting for input from Thonny’s user (since Thonny is controlling the REPL). This can be a bit counterintuitive: on-device you’d press the PicoCalc keys, but in Thonny you type on your PC keyboard. Most pure-Python logic will be identical in both cases, but anything interacting with hardware or expecting a particular interface might need adjustments when switching context.

In summary, the on-device REPL is the primary interface intended by the custom firmware (complete with a full-screen editor accessible by calling `edit("filename.py")` ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=use%20pc_terminal,LCD%20refreshing))). The serial REPL is available for development convenience, but the two are mutually exclusive in normal operation. Understanding that `import` on the device does not equate to “running as script” is crucial – one should either use the provided `run()` utility or structure the code to execute on import for consistent behavior. The firmware’s design assumes the PicoCalc itself is the “host” for running programs, with Thonny/USB as a backup or development link.

## 3. MicroPython Capabilities & Limitations on PicoCalc

**Included Modules and Features:** The PicoCalc’s MicroPython firmware is based on the RP2040 MicroPython port, with additional drivers and modules frozen into it. All the standard MicroPython modules for RP2040 are present (e.g. `machine`, `uos/os`, `time`, `gc`, etc.), and the developers added custom ones for PicoCalc’s hardware:
- `picocalcdisplay` – low-level C module for the LCD (handles SPI init, low-level drawing routines, and the dual-core update loop) ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=Fully%20functional%20and%20tested,seamlessly%20with%20vt100%20terminal%20emulator)).
- `vtterminal` (often accessed via `import vt`) – C module implementing a VT100 terminal emulator that integrates with the display and keyboard ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=The%20REPL%20and%20editor%20both,bug%20fixes%20and%20additional%20features)).
- `picocalc` – a Python module that provides high-level classes `PicoDisplay` and `PicoKeyboard` built on the above C modules, plus possibly utility functions. This abstracts the raw drivers into convenient objects ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=class%20PicoDisplay%28framebuf)) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=class%20PicoKeyboard%3A)).
- `picocalc_system` – a Python module with utility functions like `run(filename)`, `files()`, memory info, etc., to enhance the REPL as a mini shell ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=gary_m%20%20April%2017%2C%202025%2C,11%3A22pm%20%2012)) ([PicoCalc-micropython-driver/pico_files/modules/picocalc_system.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc_system.py#:~:text=def%20files%28directory%3D)).
- `pye` – a text editor module (based on robert-hh’s MicroPython editor) to allow on-device code editing ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=Image%3A%20editor%20%20Editor%20is,Now%20with%20keyword%20highlighting%20support)).
- Potentially others like `sdcard` – a driver to interface with the SD card slot (if not using the built-in one from `machine`). The forum post indicates using an `sdcard.py` module with specific wiring ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=Image%3A%20%3Afloppy_disk%3A%20SD%20Card%3A)), and the firmware’s source includes an `initsd()` function to mount the SD card at `/sd` on startup ([PicoCalc-micropython-driver/pico_files/main.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/main.py#:~:text=Separated%20imports%20because%20Micropython%20is,super%20finnicky)).

In addition, certain builds of the firmware bundle extra libraries:
- The “ulab + Eigenmath” build includes `ulab` (a numpy-like array module) and an `eigenmath` module for symbolic math. These are memory-intensive, so the firmware allocates a large chunk of heap for Eigenmath in boot ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=Using%20eigenmath)). These advanced features turn the PicoCalc into a more “full-featured” calculator, but they consume a lot of RAM (e.g. ~300KB for Eigenmath initialization ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=Using%20eigenmath))).
- The Pico W / Pico 2W variant of the firmware likely includes `network` modules for Wi-Fi (since the Pico W has wireless). However, **Wi-Fi usage is limited by a bus conflict:** the ESP32 SPI Wi-Fi chip on Pico W shares the SPI bus with the LCD. The developers note that you must stop the LCD auto-refresh before using Wi-Fi, and then restart it after ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=,picoW%2F2W)). They provide `pc_display.stopRefresh()` (or `pc_terminal.stopRefresh()`) to pause the screen update thread, allowing the SPI bus to be used for Wi-Fi, then `...recoverRefresh()` to resume the display refresh ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=,picoW%2F2W)). This is an important limitation: you can’t have smooth screen updates and active Wi-Fi at the same time.

**Differences from Standard MicroPython:** The core Python language features are unchanged, but some MicroPython APIs may not be applicable or behave differently on PicoCalc:
- **Display/Console:** Normally, MicroPython on Pico has no built-in display or console; on PicoCalc, the console is the LCD. Functions like `print()` and `input()` are redirected to the vt100 console. This means that ANSI terminal control codes (color, cursor movement) could be interpreted by the vt100 emulator – a program could, for example, use `print("\x1b[2J")` to clear the screen, which wouldn’t make sense on a stock Pico but does on PicoCalc. Conversely, error messages or tracebacks that would appear on a serial terminal now appear on the LCD. There is a learning curve to managing screen output vs. serial output. (The firmware retains the ability to write directly to USB serial; for instance, `pc_terminal` saves the original `sys.stdin` as `_usb` so developers can send debug messages to USB using `usb_debug()` in code ([PicoCalc-micropython-driver/pico_files/main.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/main.py#:~:text=pc_terminal%20%3D%20vt.vt%28pc_display%2Cpc_keyboard%2Csd%3Dsd%29)) – useful if the screen is occupied.)
- **Keyboard Input vs UART:** Instead of typing on a PC keyboard via USB, you use the PicoCalc’s keys. The keyboard is not a standard input device like `machine.UART`; it’s read through the custom driver. However, through the vt100 integration, it **acts** like a keyboard to MicroPython. One limitation is that certain key chords or special keys are hardwired in the firmware. For example, the driver treats key combinations to generate proper VT100 sequences for arrows, Ctrl+C, etc. ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=for%20i%20in%20range)) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=else%3A)). If a program wanted raw key codes, it would need to bypass the vt layer and call `pc_keyboard.keyEvent()` directly to get the low-level code. This is more complex than reading ASCII from `sys.stdin` as one might do on a normal MicroPython UART REPL.
- **Threading and Multitasking:** The standard RP2040 MicroPython supports `_thread` (to run Python code on the second core). In PicoCalc’s firmware, core1 is dedicated to the display refresh thread (which is implemented in C). Using `_thread` to start a new Python thread on core1 is likely **not possible** or not safe, since core1 is already running driver code. This is a trade-off: you gain a smooth, non-blocking display, but you effectively lose the ability to run arbitrary Python on the second core. Any attempt to use `_thread` may fail or cause conflicts. (In principle, advanced users could stop the auto-refresh and then launch their own thread, but that would disable the screen updates – not usually desirable).
- **Memory and PSRAM:** The Pico 2 and 2W have 2MB on-chip SRAM and (in the ClockworkPi model) an additional 8MB external PSRAM. As of early 2025, MicroPython has added support for the external PSRAM (by splitting the heap) ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=cmake%20..%20,DMICROPY_BOARD%3DPIMORONI_PICO_PLUS2%20make)), but it requires special configuration. The PicoCalc firmware maintainers were actively working on enabling this for the Pimoroni Pico Plus board (which is similar hardware) ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=cmake%20..%20,DMICROPY_BOARD%3DPIMORONI_PICO_PLUS2%20make)). If using a firmware build without PSRAM support, the extra 8MB is unused ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=Image%3A%20%3Aprohibited%3A%20PSRAM%3A)). This means on those devices the usable heap might still be ~600KB (internal RAM minus what’s used by firmware/drivers). With PSRAM enabled, heaps can be larger but with performance cost. In any case, a user must be mindful of memory constraints—especially when using features like Eigenmath or large buffers. The firmware’s inclusion of `memory()` (to show free/total RAM) ([PicoCalc-micropython-driver/pico_files/modules/picocalc_system.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc_system.py#:~:text=def%20memory)) ([PicoCalc-micropython-driver/pico_files/modules/picocalc_system.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc_system.py#:~:text=total_memory%20%3D%20free_memory%20%2B%20allocated_memory)) and the practice of early allocation for big modules ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=Using%20eigenmath)) highlights the need to manage memory carefully on PicoCalc.
- **File System and SD Card:** The MicroPython internal flash (2MB on Pico, 16MB on some Pico W) is available as the root filesystem. The ClockworkPi kit includes a high-speed SD card (likely mounted as `/sd`). The firmware includes drivers to mount the SD at boot (via `initsd()`), so in most cases you can access files on the SD at path `/sd/...`. A limitation is that the SD card lines are also on the same SPI controller as something (they gave wiring for SPI0 lines 16-19 for SD ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=,module%20with%20this%20wiring)), which should be independent of SPI1 used by LCD, so that’s fine). When listing files, note that internal storage is separate from SD; the provided `files()` utility (like `ls`) works on a given path ([PicoCalc-micropython-driver/pico_files/modules/picocalc_system.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc_system.py#:~:text=,specified%20directory)). One should avoid writing excessively to internal flash (to not wear it out) and prefer using the SD for heavier storage. Also, **the firmware had two distribution modes**: one with a pre-loaded filesystem (including `main.py`, editors, etc.), and one “no filesystem” UF2 where you keep your existing files. If using the latter, you must manually copy `main.py`, `picocalc.py`, etc., to the Pico’s flash ([GitHub - zenodante/PicoCalc-micropython-driver at 58635637e7fddc743614d58818cf78f0b9425863](https://github.com/zenodante/PicoCalc-micropython-driver/tree/58635637e7fddc743614d58818cf78f0b9425863#:~:text=Installation)) ([GitHub - zenodante/PicoCalc-micropython-driver at 58635637e7fddc743614d58818cf78f0b9425863](https://github.com/zenodante/PicoCalc-micropython-driver/tree/58635637e7fddc743614d58818cf78f0b9425863#:~:text=,etc)). Once set up, though, using Thonny to manage files is straightforward ([GitHub - zenodante/PicoCalc-micropython-driver at 58635637e7fddc743614d58818cf78f0b9425863](https://github.com/zenodante/PicoCalc-micropython-driver/tree/58635637e7fddc743614d58818cf78f0b9425863#:~:text=,etc)).
- **Audio and Other Hardware:** The PicoCalc hardware has a pair of PWM speakers, a 3.5mm jack, and a volume knob. The MicroPython firmware does not have a dedicated high-level audio module, but you can use `machine.PWM` on the GPIO pins (GPIO26 and 27 were found to output audio in tests ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=,troubleshooting%20sound%20because%20of%20this))) to generate sound. The volume knob likely adjusts an analog amplifier (so it won’t be readable by MicroPython directly, except maybe via an ADC pin if wired). There is also a RGB LED and possibly a vibrator motor on the board (not confirmed here). Those would need separate drivers if present. In general, any hardware beyond the core display/keyboard might require custom code. The **power management** (charging, battery percentage) is handled by the STM32 keyboard controller, which exposes battery voltage via an I2C register. The `PicoKeyboard.battery()` method returns a value (probably two-byte ADC reading) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=def%20battery)) which can be interpreted as battery level.

**Programming Constraints vs Generic MicroPython:** Developing on PicoCalc is slightly different from a stock microcontroller:
- You have a full interactive display, which is great, but it also means you must consider the **state of the display** when writing programs. For instance, if you want to use the display for graphics, you should **pause the VT100 terminal** or use its frame buffer directly to avoid clashes. Drawing arbitrary graphics while the REPL is also writing text can lead to a garbled screen.
- If your program uses the display, you have to decide whether to use **text mode or graphics mode**. Text mode (via prints or the `vt` emulator) is convenient for simple output and leverages the existing 16-color buffer. If you need more colors or pixel-level control (for games, etc.), you might be tempted to reinitialize the display in RGB565 mode. It’s possible (the `PicoDisplay` class supports different color modes ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=self.buffer%20%3D%20bytearray%28self.width%20,4bpp%20mono))), but doing so while the VT terminal is active can cause conflicts. A safer approach is to stick with the mode that’s already in use (16-color) to avoid memory reallocation. In essence, the program should **cooperate with the firmware’s initialized state**.
- The **keyboard input** is non-trivial to handle outside of the REPL. If you write a Python loop to read keys, you will likely use `pc_keyboard.readinto()` or `keyEvent()` rather than `input()`, especially if you want non-blocking or immediate key reactions. This is a lower-level style of coding (more like handling key scan codes). The provided environment largely expects you to use input in the context of REPL or in text-based programs. For game-like programs, you’ll need to poll the keyboard. The device doesn’t generate interrupts for keys, so polling in a loop with `time.sleep_ms()` is the way.
- Certain MicroPython standard libraries or functions might be absent or not tested. For example, file I/O works, but the performance to SD card might be limited by SPI speed. The device likely doesn’t have networking unless you use the Pico W. Bluetooth is not present (no BT on Pico W by default). Camera or other expansions would require additional hardware and drivers.

In summary, the PicoCalc’s MicroPython is quite powerful – it turns the Pico into a mini handheld computer with a full keyboard and screen. But the user must be mindful of the custom environment. Many incompatibilities arise not from missing modules, but from the fact that the device isn’t a typical headless MCU. Instead of printing to a serial console and reading from a PC, you’re dealing with a local display and an embedded keyboard. The ClockworkPi team has provided the necessary tools to manage this (vt100, drivers, editors), but it’s important to follow their patterns (e.g., use the given `pc_display` rather than directly toggling SPI pins, use `stopRefresh()` when doing certain operations, etc.). When writing code for PicoCalc, one should treat it almost like writing for a small terminal computer or vintage PC: consider the screen mode, cooperative multitasking (no true threading), and limited memory. As long as those constraints are respected, you can write stable programs for the PicoCalc in MicroPython.

## 4. Common Issues and Their Causes

**Issue 1: Black Screen When Importing a Program on-device (Display Re-initialization).** A known problem is that if you import or run a user program on the device that attempts to initialize the display again, the screen can go blank and the device becomes unresponsive until reboot. The cause is that the display was **already initialized and in use by the vt100 terminal**. When the user program calls something like `display = PicoDisplay(320,320)` a second time, it re-runs `picocalcdisplay.init()` on the LCD ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=super%28%29)). This can disrupt the ongoing refresh loop or allocate a new frame buffer that isn’t being fed to the LCD. Essentially, the program “steals” the display from the REPL. Since the original `pc_terminal` was drawing to the old frame buffer, and core1 might now be referencing an outdated pointer, no further updates occur – hence a black or frozen screen. The vt100 terminal’s state is also confused by another entity controlling the display. In some cases, double-initializing the SPI LCD can even hang the bus. The **recommended practice is to avoid re-initializing the display**. Instead, user code should use the existing `pc_display` object (which is a FrameBuffer). You can clear it or draw on it as needed, but you shouldn’t call its `init` again. If a program absolutely must switch display modes (say to full 16-bit color), one should first stop the auto-refresh thread (`pc_display.stopRefresh()`), then possibly re-init (or better, use a different drawing method), and later restore things. However, this is advanced and not typically needed for menu-driven apps. In short, the black screen on running a program indicates that the program likely conflicted with the vt100 display context. To fix this, do not call `PicoDisplay()` in your script – the firmware already did that. Use the one provided by the environment. (If you’re writing a standalone script via Thonny without `main.py`, then you *would* need to init the display, but on-device you generally wouldn’t.)

**Issue 2: Code run via Thonny requires separate initialization (missing display/keyboard setup).** This is essentially the flip side of the above. When you connect via Thonny after a fresh reset (especially with `main.py` suppressed), you get a blank slate MicroPython – the on-board display is not set up to mirror the REPL unless `os.dupterm` was called. So if you run a script from Thonny that tries to use the PicoCalc’s screen or keyboard, it may fail because those drivers weren’t started. For example, if you do `import picocalc` and try to use `PicoDisplay`, you might find that no output appears on screen, because you didn’t start the auto-refresh thread. The symptom is that nothing happens until you explicitly initialize things. In practice, if you want to run code via Thonny that uses the hardware, you should first run the same initialization as `main.py` does (or simply call `main.py`). Alternatively, if you **power the device normally (running `main.py`) and *then* connect Thonny**, you might find that Thonny’s REPL is not functional (since vt took over). Some users do the following: boot with device (screen shows REPL), then plug in USB and use Thonny’s file tools to edit/upload code, but not use Thonny’s Run. Instead, they go back to the device to `import` or use the editor. If you try to use Thonny’s Run in that situation, it might try to soft-reboot and you’d lose the vt context, or it will conflict with the running vt. In summary, code run remotely often “requires separate initialization” because the *automatic* init that happens on device boot was bypassed. The safe approach for remote execution is to mimic what `main.py` does: mount the SD, initialize display (`PicoDisplay(...)`), keyboard, and vt (if you want output on screen). If you only need serial output, you can skip vt and just use print which goes to Thonny. But any GUI or keyboard usage will need the drivers. This is a trade-off for using the convenience of Thonny – the environment isn’t exactly the same as the self-hosted one.

**Issue 3: Programs behave differently when imported vs. run (main() not called).** This was touched on earlier: Many Python programs (especially those written for PC) use the `if __name__ == "__main__":` idiom to only execute certain code when the script is run directly. In MicroPython on the device, there is no direct “run” command; you use `import`. When you do `import myapp`, MicroPython will set `__name__ = "myapp"` inside that module, so any code under the `if __name__ == "__main__":` block will **not execute**. This can make it seem like the program “did nothing.” For example, if `myapp.py` contains a `main()` function and only calls `main()` in that guard block, then `import myapp` will load the module and define `main()` but never call it. On a PC (running `python myapp.py`), `__name__` would be `"__main__"` and it would run. This is a common stumbling block. The result is the user sees no output on the device. Then if they connect Thonny and click Run, Thonny does execute the file such that the guard passes (it effectively runs it as a script), and the program runs – hence the user perceives “it works in Thonny but not when I import on the PicoCalc.” The **solution** is either to remove the `__main__` guard (for code intended to be imported on the device), or to explicitly call the main function after import. For instance, on the PicoCalc you could do: 
```python
import myapp
myapp.main()
``` 
to force it to run. Another solution is to use the provided `run("myapp.py")` utility which internally does an `exec` on the file contents ([PicoCalc-micropython-driver/pico_files/modules/picocalc_system.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc_system.py#:~:text=try%3A)), achieving the effect of a direct run. The key point is that **importing a module is not the same as executing a script** in MicroPython. This is an inherent Python behavior, not specific to PicoCalc, but it’s more pronounced here because the typical way to launch something on-device is by import. When designing code for PicoCalc, you might actually avoid the `if __name__ == "__main__"` pattern and instead let the module execute its logic on import (or always use the run function to execute it). Keep in mind that after an import, the module stays in memory. If you try to import again, it won’t run again. You’d need to either reset the device or use `importlib.reload`. So, if you are iterating on code, using the `run()` helper is often more convenient as it truly re-executes the file each time.

**Issue 4: Program requires extra init or behaves oddly when run via menu/Thonny vs REPL (input handling).** Another subtle issue is input and output handling differences. Suppose you wrote a game that listens for key presses in a loop. On the device, you might attempt to use `sys.stdin.read(1)` to get key inputs. However, in the vt100 environment, `sys.stdin` is tied to the vt terminal, which by default is line-buffered for the REPL. This means your program might not receive characters until Enter is pressed, unless you bypass vt’s buffering. The PicoCalc keyboard driver does not automatically feed every key to MicroPython unless MicroPython is actively reading from stdin. To get immediate key events, you would use the keyboard object’s methods (bypassing stdin). Conversely, if your program expects standard input from the user (like calling `input()`), on device the user would type and press Enter, whereas in a Thonny run, you’d type into Thonny’s prompt and press Enter. These differences can cause confusion (e.g. “my program didn’t pause for input on device, it just kept going”). Usually, that’s because a stray newline was left in the buffer or the program didn’t actually call input. In short, **programs that assume a certain I/O context might misbehave when that context isn’t present**. The remedy is to explicitly handle I/O with the available interfaces: use `pc_keyboard` for real-time key capture, and use prints or the display frame buffer for output, rather than assuming a certain terminal behavior.

**Recovery and Stability:** A design goal for PicoCalc is that if a program crashes or misbehaves, you shouldn’t have to hard-reboot the device (which could be tedious). Thanks to MicroPython’s exception handling, most errors will just drop you back to the REPL (the vt100 will display the traceback). You can then fix your code or try again. However, certain failures (like the black screen scenario where the refresh thread is confused) might effectively hang the UI. In those cases, you might still be able to use the PC serial to `Ctrl+C` or reset, but assuming both interfaces are unresponsive, a power cycle is needed. One particular case is if a program enters an infinite loop and ignores input – on a normal MicroPython board you’d press Ctrl+C in the serial terminal. On PicoCalc, you can press **Ctrl+C on the device’s keyboard** (which is actually pressing the physical Ctrl key and C key together). The keyboard driver will emit a character 0x03 (ETX) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=if%20self)), which MicroPython recognizes as a KeyboardInterrupt signal. This should break you out of the running program back to the REPL, without resetting the device. Thus, even without a PC, you have a way to interrupt a runaway script. If that fails, holding the Pico’s BOOT/RESET button or toggling the power switch can reset the system.

To summarize these issues:
- Always use the pre-initialized hardware objects instead of re-initializing – this avoids conflicts (no black screens).
- If running code via Thonny or without the stock `main.py`, remember to init the display/keyboard or limit yourself to serial output.
- Understand Python’s import model – using the provided `run()` can simplify running scripts reliably ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=Currently%20there%E2%80%99s%20some%20useful%20helper,if%20you%20type)).
- Handle input according to the context – e.g., don’t rely on interactive prompts if not appropriate, or ensure the user knows when to press Enter.
- Use `Ctrl+C` to recover from stuck programs and design your menu/launcher (next section) to catch exceptions so that even if a program errors out, the menu returns rather than leaving a broken state.

## 5. Designing a Dynamic Menu System for PicoCalc

To improve user experience, we want a simple **text-based menu that launches programs**. This menu should appear on boot (instead of the raw REPL) and allow navigating and running Python scripts stored either on the internal flash or the SD card. Here are the key design considerations and how to implement them:

### 5.1 Auto-Start at Boot

We can make the menu run automatically by placing it in `main.py`. Since MicroPython executes `boot.py` then `main.py`, we will use `boot.py` to set up the hardware (as currently done) and have `main.py` contain the menu program. This way, whenever the PicoCalc powers on (under normal conditions), the menu will start. If needed, we can add a mechanism to bypass the menu for development: for example, in `main.py` check if a certain key is held at boot or if the device is connected to USB, and if so, skip the menu and instead drop to REPL. One approach is to read the VBUS voltage via a Pin (RP2040 GP24 is typically the USB power detect). If VBUS is present, we assume a dev PC is connected and we could `return` immediately from `main.py` to keep the serial REPL free ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=Image%3A%20%3Awarning%3A%20Notes%20%26%20Caveats%3A)). Another approach is to check for a specific key combo (perhaps the user holding Esc or a particular Fn key during boot) by scanning the keyboard in `boot.py`. That may be complex, but the USB detect is simpler. We can incorporate this such that advanced users can still access Thonny easily, while normal users get the menu.

For example, at the top of `main.py`:
```python
from machine import Pin
if Pin(24, Pin.IN).value() == 1:   # USB connected
    print("USB serial detected, skipping menu and going to REPL.")
    raise SystemExit  # end main.py early, go to REPL
```
This would effectively abort the menu if USB is connected, leaving the REPL on USB (since if we skip calling `os.dupterm` again, the original USB REPL might still be active, depending on boot.py logic). In practice, test and adjust this logic to ensure it doesn’t interfere when not needed. The menu itself will be written in Python (no need for C code) and can leverage the existing drivers.

### 5.2 Listing `.py` Files from Internal Storage and SD Card

MicroPython’s `uos.listdir()` (or `os.listdir()` since `uos` is usually aliased to `os`) allows us to get a list of files in a directory. The internal flash is the root `"/"`, and the SD card is `"/sd"` (once mounted). We will gather all files ending in `.py` from both locations. One consideration: we might want to exclude system files (like `boot.py`, `main.py`, and any library modules) from the menu, to avoid confusion. It’s likely user scripts will be in a specific folder or have unique names. For simplicity, we can list everything and then filter out known names like `boot.py`, `main.py`, `picocalc.py`, etc. 

We should also perhaps separate the listing or indicate where the file resides (internal or SD). A simple way is to prefix SD card files with an identifier. For example, we could list files as:
- `program1.py` (if on internal flash)
- `sd:/game1.py` (if on SD card)

That way the user knows the location. When running the file, we will also need the path (so we know how to open it).

To implement:
```python
import os
internal_files = [f for f in os.listdir("/") if f.endswith(".py")]
sd_files = []
try:
    sd_files = [f for f in os.listdir("/sd") if f.endswith(".py")]
except Exception:
    pass  # SD card might not be present or mounted
# Filter out menu or system files:
for sysf in ("boot.py", "main.py", "picocalc.py", "picocalc_system.py"):
    if sysf in internal_files: internal_files.remove(sysf)
# Construct display list
menu_entries = [("Flash", fname) for fname in internal_files] + [("SD", fname) for fname in sd_files]
menu_entries.sort(key=lambda x: x[1].lower())  # sort by filename, case-insensitive
```
Now `menu_entries` might look like `[("Flash","demo.py"), ("SD","game1.py"), ("SD","utils.py"), ...]`. We can format these for display.

### 5.3 User Interface: Scrolling and Selection

We will use the PicoCalc’s display in text mode via the vt100 terminal for simplicity. That means we can use ANSI escape codes or just print new lines. The screen is 320x320 with 6x8 pixel font (from vt100), so roughly 53 characters per line and 40 lines. Our menus won’t exceed that typically. If there are many files, we might need scrolling (if > 38 items or so). Implementing scrolling: we can show a page of entries and update which part is visible as the user moves. But given 40 lines of space, it’s unlikely the user will have more than that many scripts. Even if they do, we could use a simple up/down that moves a highlight bar and automatically scrolls the list when the selection goes off-screen.

**Displaying the menu:** We can clear the screen and then print a title and the list of files. The currently selected item can be indicated by an arrow `->` or by inverting colors. In vt100, we can possibly use reverse video mode for a line (by printing `ESC[7m` to turn on inverse, and `ESC[0m` to turn it off). For simplicity, using an arrow or a marker is fine. For example:
```
Select a program to run:
  demo.py
-> game1.py
  test.py
```
Here `->` indicates the current selection. If the user presses Down, we move the arrow to the next item and so on.

We need to capture key presses. We have two main options:
- **Use the vt100 input via stdin:** i.e., call `sys.stdin.read(1)` or similar to get characters. The arrow keys will come through as multi-byte escape sequences: Up = `0x1B 0x5B 0x41` (`ESC [ A`). If we go this route, we have to parse those. It’s doable: read one char at a time, if it’s ESC (27) then peek the next two. This requires a non-blocking or peeking mechanism since `sys.stdin.read()` might block until a full sequence or newline. MicroPython’s `sys.stdin` on dupterm might not deliver bytes one by one easily unless in raw mode. This could complicate matters.
- **Use the keyboard driver directly:** The `PicoKeyboard` object can give raw key events without waiting for Enter. We saw how `pc_keyboard.readinto(buf)` assembles keys into a buffer, and how arrow keys are translated in that method ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=if%20key%20%3D%3D%200xB4%3A)). However, we can bypass vt’s translation by reading the hardware events ourselves. The function `pc_keyboard.keyEvent()` returns a 2-byte result: the first byte is the key state (pressed, released, etc.) and second is the key code ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=def%20keyEvent)). We can call `pc_keyboard.keyEvent()` repeatedly to fetch events from its FIFO. Alternatively, we could use `pc_keyboard.readinto()` with a buffer to get processed characters (which would yield actual ESC, '[', 'A' bytes for arrow), but then we’d still parse them. It might be simpler to use `keyEvent` and interpret the key codes directly:
  - According to the driver, when a key is pressed, state will be `_StatePress` (constant 1) or `_StateLongPress` (2) for a long hold ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=_StateIdle%20%3D%20const)) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=key%20%3D%20keyGot)). When released, state is 3. We likely care about presses.
  - Key codes: from the code, 0xB5 = Up, 0xB6 = Down, 0xB4 = Left, 0xB7 = Right ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=if%20key%20%3D%3D%200xB4%3A)). Enter is 0x0A (line feed) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=self.hardwarekeyBuf.extend%28b%27)), Backspace is 0x08, Escape is 0xB1 ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=elif%20key%20%3D%3D%200xB1%3A%20,KEY_ESC)). Regular letters likely correspond to their ASCII codes (e.g., 'A' = 0x41 when Shift is off for uppercase or something – but since it’s a qwerty, it likely sends ASCII for letters).
  - We have to be mindful that the driver, in `keyEvent()`, does not apply the VT translation; it gives raw code and state. This is perfect for our needs because we can decide “if Up pressed, move selection”.

We will implement a loop that checks for key events in a non-blocking way. We can use `time.sleep_ms()` for a short delay to avoid 100% CPU. Since MicroPython isn’t multi-threaded here, this loop will effectively lock the device into the menu until something is chosen (which is what we want).

Pseudo-code for menu loop:
```python
selection = 0
offset = 0  # for scrolling, if needed
while True:
    # Display menu
    os.dupterm(pc_terminal)  # ensure output goes to screen (should already be the case)
    print("\x1b[2J\x1b[H")   # clear screen and move cursor to top-left (vt100)
    print("=== Program Launcher ===\n")
    # Determine which entries to show (for scrolling):
    total = len(menu_entries)
    max_lines = 36  # leave some lines for header or instructions
    if total <= max_lines:
        start_index = 0
        end_index = total
    else:
        # if selection near bottom, scroll
        if selection < offset: offset = selection
        elif selection >= offset + max_lines: offset = selection - max_lines + 1
        start_index = offset
        end_index = min(offset + max_lines, total)
    # Print the visible entries
    for i in range(start_index, end_index):
        src, fname = menu_entries[i]
        prefix = "-> " if i == selection else "   "
        location_tag = "(SD)" if src == "SD" else "    "
        # Print the line with an arrow on selected, and maybe mark SD files
        print(f"{prefix}{fname:40} {location_tag}")
    print("\nUse arrow keys to navigate, Enter to run, ESC to exit.")
    # Key handling
    key = None
    while key is None:
        event = pc_keyboard.keyEvent()
        if event is None:
            time.sleep_ms(50)
            continue
        state, code = event[0], event[1]
        if state == 1:  # _StatePress
            if code == 0xB5:   # Up arrow
                key = "up"
            elif code == 0xB6: # Down arrow
                key = "down"
            elif code == 0x0A: # Enter (0x0A line feed as per driver)
                key = "enter"
            elif code == 0xB1: # Esc key
                key = "quit"
            # (We ignore left/right in menu or other keys)
    # After getting a key:
    if key == "up":
        if selection > 0:
            selection -= 1
        else:
            selection = total - 1  # wrap-around to bottom
        continue  # redraw loop
    if key == "down":
        if selection < total - 1:
            selection += 1
        else:
            selection = 0  # wrap to top
        continue
    if key == "quit":
        print("Exiting to REPL...") 
        break  # break out of menu loop, drop to REPL
    if key == "enter":
        chosen_src, chosen_file = menu_entries[selection]
        file_path = ("/sd/" + chosen_file) if chosen_src == "SD" else ("/" + chosen_file)
        print(f"\nRunning {chosen_file} from {chosen_src}...\n")
        run(file_path)  # use the helper to execute the file
        print("\n<< Press any key to return to menu >>")
        # Wait for a key press to continue
        while pc_keyboard.keyEvent() is None:
            time.sleep_ms(100)
        # After a key press, loop will redraw menu
        # Optionally, recover screen refresh if it was stopped by program:
        pc_display.recoverRefresh()
        selection = 0  # or keep last selection
        # continue the menu loop
```

This is conceptual – you’d refine it with proper imports and error handling. Notably, we use the `run()` function (we can import `run` from `picocalc_system` or implement similarly) to execute the chosen program. Using `run()` ensures the script runs in a clean context and doesn’t remain imported, and it catches exceptions internally, printing them to the console without crashing our menu program ([PicoCalc-micropython-driver/pico_files/modules/picocalc_system.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc_system.py#:~:text=try%3A)). We wrap the execution so that once the program finishes (or even if it errors or is interrupted), we return to the menu. We prompt the user to press a key to acknowledge before returning to the menu list – this gives them a chance to see any output the program produced (otherwise the menu might clear the screen immediately). 

Crucially, we also handle **KeyboardInterrupt** inside `run()` or around it. The `picocalc_system.run` already catches generic `Exception` and prints it ([PicoCalc-micropython-driver/pico_files/modules/picocalc_system.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc_system.py#:~:text=print%28f)), but it may not explicitly catch KeyboardInterrupt (which is an Exception too, so it probably will catch it as “an error occurred: KeyboardInterrupt”). If we want to allow the user to abort a running program back to the menu, we might not even need to modify `run()`. The user can press Ctrl+C on the device; MicroPython will raise a KeyboardInterrupt, which the `run` function catches as a generic exception and prints. That would drop back to our menu loop as soon as `run()` returns. We can detect this by checking if the exception was KeyboardInterrupt if we want to avoid printing it as an error. A simpler way: we could wrap `run()` in our own try/except:
```python
try:
    exec(open(file_path).read(), {})
except KeyboardInterrupt:
    print("\n[Program interrupted by user]")
except Exception as e:
    print(f"\n[Program error: {e}]")
```
But since `picocalc_system.run` already does something similar (without isolation of globals), we might just use it and not worry too much.

**Non-interference with Thonny REPL:** By running the menu in `main.py`, we inherently take over the REPL (the menu loop is an active Python program). If a developer connects Thonny in the middle of this, they won’t be able to use the REPL because our code is running. The earlier strategy of skipping the menu when USB is present is important here. With that in place, when a user is actively using Thonny (i.e. the device is plugged in and reset), they’ll get a REPL instead of menu, so no interference. If, however, the device is already running the menu and then the user connects a PC, the menu has no knowledge of that – it will keep running. In that case, the user can still press Ctrl+C from the PC which sends an interrupt to stop the menu. But if vt is controlling input, that might not reach. This corner case might require a manual reset. 

A more elegant approach could be: detect USB connect at runtime via the USB VBUS or by periodically checking if `sys.stdin` changed. But that’s likely overkill. Given that most users will either boot in PC-connected mode or not, we can assume the check at startup is enough. 

We also ensure that when a program is running, it uses the same `pc_terminal` for I/O, so its output doesn’t interfere with Thonny. In fact, during normal standalone use, Thonny isn’t connected, so no issue. If Thonny is connected but we skipped the menu, then the program wouldn’t be auto-run anyway. Essentially, as long as we don’t try to have both menu and Thonny controlling the board simultaneously, we are fine.

### 5.4 Sharing Initialized Display/Keyboard Objects

As emphasized, the menu and the launched programs should reuse the existing `pc_display` and `pc_keyboard`. In our design, `boot.py` has already created those (or we can import the `picocalc` module to get them if they were set as globals). In the older firmware, `main.py` itself did the initialization and made `pc_display`, `pc_keyboard`, and `pc_terminal` global ([PicoCalc-micropython-driver/pico_files/main.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/main.py#:~:text=pc_display%20%3D%20PicoDisplay%28320%2C320%29)). If we adopt the new approach where `boot.py` does it, then `main.py` (our menu) might need to import those globals. Possibly the firmware put them in the builtins or `picocalc` module. If not, we could simply do the initialization in our main as well (since the drivers can handle double init? But we’d rather not double init). 

One solution: in `boot.py`, after creating the objects, assign them to `builtins`:
```python
import builtins
builtins.pc_display = PicoDisplay(...)
builtins.pc_keyboard = PicoKeyboard(...)
builtins.pc_terminal = vt.vt(pc_display, pc_keyboard, sd)
os.dupterm(builtins.pc_terminal)
```
This would make them accessible in `main.py` without import. If that’s not the case, an alternative is to do:
```python
from picocalc import PicoDisplay, PicoKeyboard
import vt, os
# If not already done in boot.py:
pc_display = PicoDisplay(320, 320) 
pc_keyboard = PicoKeyboard()
pc_terminal = vt.vt(pc_display, pc_keyboard)
os.dupterm(pc_terminal)
```
But doing that again risks the black-screen issue. So ideally we rely on boot.py’s work. In our pseudocode above, we used `pc_display`, `pc_keyboard` as if they exist. In practice, we’d obtain them from somewhere. Possibly `picocalc_system` or `picocalc` might expose references or singletons. We might need to structure the code carefully to avoid reinitialization.

For the menu’s operation itself, we share these objects. We use `pc_keyboard.keyEvent()` to get key presses. We use `pc_display` only at the end of running a program to ensure refresh is on (in case the program turned it off). We largely rely on `pc_terminal` (vt) for output, via `print()` statements. Since `os.dupterm(pc_terminal)` was done, all our prints go to the LCD. We don’t explicitly call `pc_display.show()` after prints – the vt driver is writing directly into the frame buffer and the auto-refresh thread is pushing it to LCD continuously. So text appears near-instantly. 

If a launched program tries to do its own graphics using `pc_display`, that’s fine – it’s drawing to the same buffer. If it calls `pc_display.stopRefresh()`, we detect that and call `recoverRefresh()` after the program ends to resume normal operation. We included `pc_display.recoverRefresh()` after returning from run. Similarly, if a program had switched the dupterm (unlikely), we should re-dupterm back to `pc_terminal` (we can call `os.dupterm(pc_terminal)` again after program execution to ensure the REPL is back on LCD). If the program raised an exception that was caught, our menu should still be in good shape to continue. We might want to flush or clear any input buffer after a program ends, to avoid a situation where a key press intended for the program is left and then picked up by the menu. In our code, after program finish, we wait for a key press to return to menu and then effectively ignore it (just using it to pause). That should clear any lingering key. We also could empty `pc_keyboard.hardwarekeyBuf` (the deque) if needed, but reading all events until None as we did achieves that.

### 5.5 Running Selected Programs Cleanly

As discussed, using the `run()` helper (or our own exec wrapper) is preferred over `import`. By executing the file content, we ensure that the program runs as if it’s the main module. It won’t leave global state in the menu’s namespace (especially if we execute it in a fresh empty dict). The provided `picocalc_system.run(filename)` essentially does `exec(open(filename).read())` ([PicoCalc-micropython-driver/pico_files/modules/picocalc_system.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc_system.py#:~:text=try%3A)), which executes in the current global namespace. In their implementation, they do it without providing an explicit globals dict, meaning it will execute in whatever scope `run` was defined (likely the `picocalc_system` module’s global scope). That could pollute things. We may consider modifying it to execute in an isolated namespace to avoid any variable collisions or memory leaks between runs. For example:
```python
def run_file(filepath):
    try:
        with open(filepath) as f:
            code = f.read()
    except OSError as e:
        print(f"Error: cannot open {filepath}: {e}")
        return
    # Execute in a fresh global dict (with builtins available)
    globals_dict = {"__name__": "__main__", "__builtins__": __builtins__}
    try:
        exec(code, globals_dict)
    except Exception as e:
        # Catch all exceptions to avoid crashing the menu
        if isinstance(e, KeyboardInterrupt):
            print("** Program interrupted by user **")
        else:
            print("** Program error:", e, "**")
```
This way each program runs with a `__name__=="__main__"` as if it’s standalone. After it finishes, its variables go out of scope (except any lingering references). This helps stability for multiple launches.

**Avoiding Interference with REPL (Thonny) during program run:** While a user program is running from the menu, the REPL is not active; the menu’s exec essentially occupies MicroPython. Thonny, if connected, would be paused/out of sync. However, since we plan to mostly use this when not connected, it’s fine. If someone did connect, they could break the program with Ctrl+C (which we catch). That would bring them back to menu (which might not be what they expect, but it’s better than nothing). If they really want REPL, they should exit the menu (we provided Esc for that). On Esc, we `break` the menu loop and thus `main.py` ends, handing control back to REPL. At that point, if USB is connected, it might still be the vt REPL unless we also detect that and maybe drop vt. We could, upon exiting menu, call `os.dupterm(None, 1)` or similar to detach vt and re-enable USB. But detaching vt is tricky once it was primary. Possibly easier: if user hits Esc to exit menu, just let them use the device’s REPL on screen (vt stays active). If they want Thonny at that point, they could still plug in and do the micro-USB reset trick or press Ctrl+A+D (if something special? maybe not applicable). Given the scope, we can assume Esc means “quit to device REPL” (not PC). Because if they wanted PC REPL, they’d have used the USB detection to skip menu in first place. 

### 5.6 Key Combo for Reset/Return to Menu

We already decided that Esc key in the menu will allow quitting the menu. That covers returning to REPL from menu. What about resetting from a running program? If a program is running and the user wants to get back to menu, pressing Ctrl+C (device) will interrupt it, and our menu catches it and goes back to menu loop. That effectively is “return to menu.” If a program hung in a way that Ctrl+C doesn’t work (which would be rare, since MicroPython should handle it unless interrupts are disabled), a last resort is the device’s reset switch. But we aim to avoid needing that.

So the combination is:
- **While in menu:** Press `ESC` to exit menu (go to REPL).
- **While a program is running:** Press `Ctrl+C` (the device’s Ctrl key + C) to interrupt and return to menu (with a message).
- Possibly define another combo like Ctrl+Esc for hard reset? But that might not be necessary with the above.

We should communicate these to the user via an on-screen hint in the menu (“ESC to quit menu, Ctrl+C in program to stop”). The menu already prints a hint for navigation and ESC. We could add a note when launching a program: “(Press Ctrl+C to abort and return to menu)”.

### 5.7 Stability Considerations

The menu should be robust:
- It runs in an infinite loop, but with blocking only on key input and sleeps, which is fine (very low CPU usage while waiting).
- It catches exceptions from launched programs, so a crash in a program does not crash the menu. We just print the error and resume.
- It resets any critical state after a program: re-enabling screen refresh and reassigning dupterm if needed. Also, it could reinitialize the keyboard if somehow that got messed (though that’s unlikely – the keyboard driver should continue working).
- If a program leaves the screen in an altered state (e.g., filled with graphics or turned off backlight), the menu will redraw over it. One thing to consider: backlight control. If a program turned off the LCD backlight via `pc_keyboard.setBacklight(0)`, the screen would go dark even though content is still being drawn. We might want to ensure the backlight is on when showing the menu. The backlight is managed by the STM32 (register BK1 for LCD backlight, BK2 for keyboard backlight) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=def%20backlight)). Possibly `PicoKeyboard.setBacklight(value)` is provided. We could store the backlight level at menu start and reapply it each time we show menu. But unless user programs play with it, not a big issue.

- Memory fragmentation: Repeatedly exec’ing scripts might fragment the heap over time. MicroPython’s GC will collect garbage, but if scripts allocate large objects and free them, fragmentation can occur. The RP2040 doesn’t have an MMU, but MicroPython’s garbage collector can compact movable objects (not absolutely defragment like a memory allocator though). For long sessions where many different programs are run, it’s possible memory gets tight. As a precaution, we could call `gc.collect()` after each program run to clean up ([PicoCalc-micropython-driver/pico_files/modules/picocalc_system.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc_system.py#:~:text=if%20k%20not%20in%20keep_vars%3A)). The `picocalc_system` code does something similar (deleting temp globals and collecting) presumably to keep the REPL environment clean between runs ([PicoCalc-micropython-driver/pico_files/modules/picocalc_system.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc_system.py#:~:text=if%20k%20not%20in%20keep_vars%3A)). We can mimic that. For instance, after `run_file()`, do `gc.collect(); gc.mem_free()`.

If memory fragmentation becomes a problem, a drastic solution is a full soft reset of MicroPython after each program. But that would lose the menu state and require reloading it – not ideal. So we stick to managing memory within the session.

- We should also ensure the menu itself doesn’t eat memory over time. Our list of files is static unless we rescan. If we wanted, we could offer an option to refresh the file list (if user inserted an SD card after boot, etc.). But maybe not needed if we scan each time we display menu (which we do only once on start in the above logic). If we wanted to rescan when returning from a program (maybe they added files via Thonny in the meantime), we could recompute the list. This might be overkill; likely the files are in place at boot.

**C-level hooks vs Python-only:** Everything described can be done in Python using existing APIs. We do not need to modify the firmware in C for the menu. We leverage the drivers that are already written in C (display refresh, vt, keyboard scanning) to handle the heavy lifting. The menu logic itself is high-level and perfectly fine in Python given the relatively low speed requirements (scanning a few keys and printing text). Scrolling text or highlighting doesn’t require high performance; the RP2040 can easily handle printing dozens of lines. The only slight overhead is that printing line by line via vt100 is not the fastest way to update a screen (versus writing directly to frame buffer), but it’s absolutely fine for a menu, which is mostly static text. The user won’t notice any lag navigating a text menu.

If we *wanted* to optimize, we could consider using the frame buffer directly: e.g., draw an arrow sprite or invert colors manually for highlight. But that would require custom drawing code and doesn’t bring much benefit. The vt100 approach also allows using any terminal control sequences if we like (color coding items, etc.). However, vt100_stm32 might have limited capabilities (the original code mentions 16-color support with a standard palette ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=,python%20script%20to%20convert%20it)), possibly corresponding to ANSI colors 0-15).

**Non-interference with REPL** specifically was mentioned – our approach ensures that when the menu is active, it *is* the REPL in a sense (the user isn’t meant to drop to a `>>>` prompt unless they exit the menu). And we provide a way to exit. The design choice is that while menu is running, you cannot simultaneously type arbitrary Python commands – you’re in the menu application. To get back to an interactive prompt, press ESC. This is acceptable because the menu is effectively a full-screen application replacing the REPL loop.

## 6. Practical Implementation and Code Examples

Below is an outline of how the menu system’s code could look. This can serve as a starting template. It assumes that `boot.py` has already initialized `pc_display`, `pc_keyboard`, and `pc_terminal` and mounted the SD card. (If not, you would include those steps in `main.py` before launching the menu loop, but in the current firmware they are taken care of in advance.)

```python
# main.py - Program Launcher for ClockworkPi PicoCalc

import os, time, gc
from picocalc_system import run  # using the provided run() function
# If picocalc_system.run executes in a shared namespace, you might use your own exec method.

# Optional: skip menu if USB serial is connected (development mode)
try:
    from machine import Pin
    if Pin(24, Pin.IN).value():
        print("USB cable detected - starting serial REPL instead of menu.")
        raise SystemExit  # End main.py, stay in REPL
except ImportError:
    pass  # machine might not be available or Pin 24 not used; ignore if so

# Ensure our output is going to the device screen
os.dupterm(pc_terminal)  # (pc_terminal should be created in boot.py)

# Gather list of python files
def list_programs():
    files = []
    try:
        for fname in os.listdir("/"):
            if fname.endswith(".py"):
                files.append(("Flash", fname))
    except Exception as e:
        print("Error listing internal files:", e)
    try:
        for fname in os.listdir("/sd"):
            if fname.endswith(".py"):
                files.append(("SD", fname))
    except Exception:
        pass  # no SD or error listing SD
    # Exclude system files
    exclude = {"boot.py", "main.py", "picocalc.py", "picocalc_system.py", "fbconsole.py"}
    files = [entry for entry in files if entry[1] not in exclude]
    # Sort by name
    files.sort(key=lambda x: x[1].lower())
    return files

programs = list_programs()
if not programs:
    print("No .py programs found on internal storage or SD card.")
    print("Upload scripts via Thonny or copy to the SD card to use this menu.")
    raise SystemExit  # nothing to do, go to REPL

current_index = 0

def refresh_menu(selected):
    """Render the menu to the screen, highlighting the selected index."""
    # Clear screen and print header
    print("\x1b[2J\x1b[H", end="")  # ANSI: clear screen and home cursor
    print("=== PicoCalc Menu ===".ljust(53) + " (ESC to exit)\n")
    total = len(programs)
    # We will show up to 15 entries around the selected to fit screen
    # (For 40-line screen, after header and footer, ~36 lines for menu)
    max_show = 36
    if total <= max_show:
        start = 0
        end = total
    else:
        # scroll window
        if selected < scroll_offset:
            scroll_offset = selected
        elif selected >= scroll_offset + max_show:
            scroll_offset = selected - max_show + 1
        start = scroll_offset
        end = min(start + max_show, total)
    for idx in range(start, end):
        src, fname = programs[idx]
        prefix = "->" if idx == selected else "  "
        loc = "[SD]" if src == "SD" else "    "
        line = f"{prefix} {fname:<40}{loc}"
        # If vt100 supports inverse video, we could use that for highlight:
        # if idx == selected: line = "\x1b[7m" + line + "\x1b[0m"
        print(line)
    print(f"\n({total} programs found. Use Up/Down + Enter.)", end="")

scroll_offset = 0

# Main menu loop
while True:
    refresh_menu(current_index)
    # Wait for key input
    key = None
    while key is None:
        event = pc_keyboard.keyEvent()
        if not event:  # no key event
            time.sleep_ms(50)
            continue
        state, code = event[0], event[1]
        if state == 1:  # key press
            if code == 0xB5:   # Up arrow code
                key = "up"
            elif code == 0xB6: # Down arrow
                key = "down"
            elif code == 0x0A: # Enter
                key = "enter"
            elif code == 0xB1: # ESC
                key = "esc"
            # ignore other keys
    # Process navigation
    if key == "up":
        current_index = (current_index - 1) % len(programs)
        continue  # refresh loop
    elif key == "down":
        current_index = (current_index + 1) % len(programs)
        continue
    elif key == "esc":
        print("\nExiting menu to REPL.")
        break  # exit the menu loop, end main.py -> REPL
    elif key == "enter":
        # Launch the selected program
        src, filename = programs[current_index]
        filepath = ("/sd/" + filename) if src == "SD" else ("/" + filename)
        print(f"\n*** Running {filename} ***\n")
        # Attempt to run the program
        try:
            run(filepath)  # executes the file (captures output on screen)
        except Exception as e:
            # If picocalc_system.run wasn't used, handle exceptions here
            if isinstance(e, KeyboardInterrupt):
                print("\n[User interrupted]")
            else:
                print(f"\n[Error] {type(e).__name__}: {e}")
        # Ensure display refresh is on (in case program turned it off)
        try:
            pc_display.recoverRefresh()
        except Exception:
            pass
        # After program ends, force a garbage collection
        gc.collect()
        print("\n*** Program finished. Press any key to return to menu ***")
        # Wait for a key press to proceed
        while pc_keyboard.keyEvent() is None:
            time.sleep_ms(100)
        # possibly refresh file list in case something changed:
        programs = list_programs()
        if current_index >= len(programs):
            current_index = len(programs)-1
        # loop continues, menu redraws
```

*(This code is illustrative; some parts (like `scroll_offset` handling) may need refinement and the key codes should be verified. It assumes certain key code values from the driver as discussed.)*

A few notes on this implementation:
- We use ANSI escape `\x1b[2J` and `\x1b[H` to clear the screen. This is supported by the vt100 emulator ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=The%20REPL%20and%20editor%20both,bug%20fixes%20and%20additional%20features)).
- Navigation is by Up/Down arrow, which we identified as 0xB5 and 0xB6 in the driver’s key codes ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=if%20key%20%3D%3D%200xB4%3A)).
- Enter is 0x0A (the keyboard sends CR/LF for Enter, but the driver specifically pushes 0x0D 0x0A into the buffer; using keyEvent, we saw it treat Enter as 0x0A on press) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=self.hardwarekeyBuf.extend%28b%27)).
- Escape is 0xB1 as per the mapping ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=elif%20key%20%3D%3D%200xB1%3A%20,KEY_ESC)).
- We handle wrap-around for selection at list boundaries.
- After running a program, we pause until a key is pressed so the user can see the program’s output or error message. The key press they hit to continue is fetched and then essentially discarded (not used for menu navigation). That’s why we refresh the menu anew after.
- We call `pc_display.recoverRefresh()` just in case the program disabled auto-refresh (for example, if it used Wi-Fi) ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=,picoW%2F2W)). If the program didn’t call `stopRefresh()`, our call is harmless.
- We also re-establish `os.dupterm(pc_terminal)` implicitly by continuing to use it – if a program tried to change the dupterm, we might need to set it back. Most user scripts wouldn’t do that, but for safety one could do `os.dupterm(pc_terminal)` again after the run.

**Using the Menu:** With this in place, when the PicoCalc boots, the user will see the menu with a list of scripts. They use the arrow keys to pick one and press Enter. The screen clears (we clear it before launching a program to give it a clean output area) and the program’s output is shown. If the program uses input(), the user can type on the keyboard as usual. When the program finishes or if they press Ctrl+C to break it, control returns to the menu. They can then launch another program or press ESC to get to the bare REPL (maybe for advanced usage).

This menu system does not require any native code modifications and works within the given MicroPython environment. It **leverages the already-initialized vt100 terminal and keyboard**, avoiding re-inits that caused the black screen issue. By catching errors and interrupts, it maintains stability: the user should rarely need to reboot, since they can always regain control (ESC or Ctrl+C). Even if a program runs amok with graphics, our recover step and clear-screen on menu will restore a usable interface.

## 7. Additional Context and Best Practices

When implementing and using this menu system on PicoCalc, keep the following in mind:

- **Adhering to PicoCalc’s environment:** Always test your menu and programs on the device itself. Some behaviors (especially related to key inputs and screen output) can only be fully validated on the actual hardware (or an emulator of it). The ClockworkPi forum and documentation are useful resources – for instance, the developer’s notes confirm details like the 16-color mode palette ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=Image%3A%20%3Aframed_picture%3A%20Framebuffer%20%26%20Graphics%3A)) and the need to remove duplicate Python files from `/lib` since they are frozen in firmware ([GitHub - zenodante/PicoCalc-micropython-driver at 58635637e7fddc743614d58818cf78f0b9425863](https://github.com/zenodante/PicoCalc-micropython-driver/tree/58635637e7fddc743614d58818cf78f0b9425863#:~:text=,etc)). Make sure your `boot.py` and `main.py` from the firmware are up to date so all features (editor, etc.) work correctly.

- **Avoid heavy computations in the menu loop:** The menu is mostly I/O bound, which is fine. Don’t do things that could block the menu for too long (like scanning a huge directory or writing to disk) without giving feedback. If an SD card is large, listing all `.py` files could take a moment – but typically that’s quick. If needed, you could implement pagination for extremely long lists to avoid slow printing.

- **Limitations in vt100:** The vt100 emulator covers most common text functions, but it may not implement everything (like complex cursor addressing beyond simple moves, or custom font sizes). For our purposes, basic escape codes suffice. If you try to get fancy (colored text output via ANSI colors, etc.), verify that those codes are recognized. The vt100 code is based on an STM32 implementation with “bug fixes and additional features” ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=Now%20with%20keyword%20highlighting%20support)), so it likely supports standard ANSI color codes (they mentioned a 16-color map ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=,python%20script%20to%20convert%20it)) for screen capture). For example, printing `"\x1b[31mRed\x1b[0m"` might show “Red” in red on the device. This could be used to differentiate internal vs SD files or highlight selection, as an enhancement.

- **Cleaning up after running programs:** We took steps to recover the display and catch exceptions. If a particular program leaves resources open (like SPI devices or large memory buffers), it’s good to either handle that in the program or in the menu. For example, if a program opens a file and doesn’t close it, it will be closed when the program’s exec context is destroyed, so that’s okay. If a program changes the volume or backlight, we might want to reset those. Currently, our menu doesn’t adjust volume/backlight, assuming user can control those via hardware knobs. If needed, one could save the state of `pc_keyboard.backlight()` at menu start and restore it each time returning to menu.

- **Future expandability:** This menu could be extended to have multiple pages or options (like a “settings” page to adjust brightness, etc.). But the core requirement was launching scripts, which we’ve addressed. If a need arises to run something other than Python scripts (like maybe MicroPython could call a native app or a binary), that would be a different story – typically not applicable here.

- **No C-level modifications required:** Our design stays entirely in Python. This means it’s easy to tweak and deploy via Thonny (just editing `main.py`). There is no need to rebuild the firmware in C or fiddle with the MicroPython internals. This keeps things simple and within the capability of the end user to modify on-device.

By implementing the above menu system, the PicoCalc becomes much more user-friendly: upon power-up it can present a list of available tools, games, or demos to run. This eliminates the need for the user to manually type Python commands to launch things, and it prevents the accidental scenario of messing up the display by reinitializing it in each script. All scripts will run under the safe umbrella of the menu’s environment.

**Stability Benefit:** If any launched program crashes, the menu catches it and returns control, which is a better experience than the device freezing or dropping to a raw REPL with potentially no on-screen prompt (imagine if the vt terminal was disrupted). We also reduce the risk of crashes by not messing with the low-level drivers after boot. 

In conclusion, the combination of proper understanding of the PicoCalc’s boot process, careful management of the vt100 terminal state, and a well-crafted Python menu program addresses the points raised:
- We’ve described how the boot process works and how vtterminal and drivers are initialized, and that knowledge guides us to avoid re-initializing them ([PicoCalc-micropython-driver/pico_files/main.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/main.py#:~:text=pc_display%20%3D%20PicoDisplay%28320%2C320%29)) ([PicoCalc-micropython-driver/pico_files/main.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/main.py#:~:text=os)).
- We distinguished the on-device REPL vs. Thonny usage and explained the import vs run differences, recommending using a `run()` function ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=gary_m%20%20April%2017%2C%202025%2C,11%3A22pm%20%2012)).
- We enumerated the capabilities and quirks of MicroPython on PicoCalc (such as Wi-Fi and PSRAM considerations) ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=,picoW%2F2W)) ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=Image%3A%20%3Aprohibited%3A%20PSRAM%3A)).
- We tackled the specific issues (black screen on re-init, needing separate init over Thonny, main() not auto-called) with clear reasons and solutions.
- And we designed a concrete solution (menu system) with code, staying within Python and maintaining stability.

By following these guidelines and using the provided code template, one can implement a dynamic launcher for the PicoCalc that significantly improves usability while respecting the device’s unique MicroPython environment.

**Sources:**

- ClockworkPi PicoCalc MicroPython driver documentation and README ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=%E2%9C%85%20Keyboard%20Driver)) ([GitHub - zenodante/PicoCalc-micropython-driver](https://github.com/zenodante/PicoCalc-micropython-driver#:~:text=Now%20with%20keyword%20highlighting%20support))  
- ClockworkPi forum insights on MicroPython port and usage caveats ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=Image%3A%20%3Awarning%3A%20Notes%20%26%20Caveats%3A)) ([PicoCalc MicroPython Port Status - PicoCalc - clockworkpi](https://forum.clockworkpi.com/t/picocalc-micropython-port-status/16669#:~:text=gary_m%20%20April%2017%2C%202025%2C,11%3A22pm%20%2012))  
- PicoCalc keyboard and display driver code (zenodante’s repository) for technical details ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=class%20PicoDisplay%28framebuf)) ([PicoCalc-micropython-driver/pico_files/modules/picocalc.py at 58635637e7fddc743614d58818cf78f0b9425863 · zenodante/PicoCalc-micropython-driver · GitHub](https://github.com/zenodante/PicoCalc-micropython-driver/blob/58635637e7fddc743614d58818cf78f0b9425863/pico_files/modules/picocalc.py#:~:text=if%20key%20%3D%3D%200xB4%3A)).
