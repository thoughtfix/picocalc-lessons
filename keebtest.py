# Keyboard test for PicoCalc
# If you don't know which key you expect to read for your own program
# this will give you the code in stdout. 

import picocalc
import time

kbd = picocalc.PicoKeyboard()

print("Starting key monitor... (press keys!)")

while True:
    event = kbd.keyEvent()
    if event:
        ev_type = 'Press' if event[0] == 1 else 'Release'
        keycode = event[1]
        try:
            keychar = chr(keycode) if 32 <= keycode <= 126 else f"({keycode})"
        except:
            keychar = f"({keycode})"
        print(f"{ev_type}: {keychar} (ASCII {keycode})")
    time.sleep(0.05)  # 20 checks per second
