# Your basic "graphical hello world" for PicoCalc
# Displays 16 color bars
# code@danielgentleman.com

import picocalc

display = picocalc.PicoDisplay(320, 320)
display.fill(0)

# Draw 16 color bars
for i in range(16):
    display.fill_rect(0, i * 20, 320, 20, i)

display.text("Hello PicoCalc!", 10, 310, 15)
display.show()
