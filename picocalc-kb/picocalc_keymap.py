# picocalc_keymap.py
# Author: [You can add your name here if you want]
# License: Apache 2.0
# Description: Maps PicoCalc keypress ASCII codes to human-readable names

KEY_MAP = {
    # Numbers
    48: '0',
    49: '1',
    50: '2',
    51: '3',
    52: '4',
    53: '5',
    54: '6',
    55: '7',
    56: '8',
    57: '9',

    # Arithmetic symbols
    46: '.',
    43: '+',
    45: '-',
    42: '*',
    47: '/',
    61: '=',

    # Special characters
    9: 'TAB',
    8: 'BACKSPACE',
    32: 'SPACE',
    165: 'ENTER',
    177: 'ESC',
    212: 'DEL',
    193: 'CAPSLOCK',
    208: 'BRK',
    210: 'HOME',
    213: 'END',
    209: 'INS',

    # Arrow keys
    178: 'LEFT',
    179: 'RIGHT',
    180: 'UP',
    181: 'DOWN',

    # F1–F10
    129: 'F1',
    130: 'F2',
    131: 'F3',
    132: 'F4',
    133: 'F5',
    134: 'F6',
    135: 'F7',
    136: 'F8',
    137: 'F9',
    144: 'F10',

    # Shift / Alt / Ctrl
    162: 'LSHIFT',
    163: 'RSHIFT',
    160: 'LCTRL',    # Defined in keyboard.h even if you didn't press it yet
    161: 'LALT',     # Captured via Alt+Ins
}

def get_key_name(ascii_code):
    """Return the human-readable name of a PicoCalc key."""
    return KEY_MAP.get(ascii_code, f"UNKNOWN({ascii_code})")

