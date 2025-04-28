# PicoCalc Keyboard Map

This module (`picocalc_keymap.py`) provides a simple way to translate raw ASCII keypress codes from the ClockworkPi PicoCalc keyboard into human-readable names.

It is intended to be reused across all PicoCalc projects: calculators, games, shells, menus, etc.

---

## Files

- `picocalc_keymap.py` — Maps raw ASCII codes to key names
- `picocalc_keytest.py` — Simple REPL test tool for manually checking mappings

---

## Usage

Import the mapping function into your project:

```python
from picocalc_keymap import get_key_name
```

Then call `get_key_name(ascii_code)` wherever you need to interpret keypresses:

```python
code = 49  # Example: ASCII for '1'
key_name = get_key_name(code)
print(key_name)  # Outputs: '1'
```

If an unmapped key is pressed, it will return `"UNKNOWN(XXX)"` for easy debugging.

---

## Features

- Full number and symbol mappings (`0-9`, `+`, `-`, `*`, `/`, `=`, `.`)
- Special keys (`ENTER`, `ESC`, `TAB`, `DEL`, `BACKSPACE`, `CAPSLOCK`, etc.)
- Full arrow keys (`LEFT`, `RIGHT`, `UP`, `DOWN`)
- F1–F10 keys
- Shift, Ctrl, and Alt modifiers recognized separately (`LSHIFT`, `RSHIFT`, `LCTRL`, `LALT`)
- Friendly to REPL development in Thonny or similar

---

## Example: Live Key Test

Use the provided `picocalc_keytest.py` to interactively test key mappings:

```bash
python3 picocalc_keytest.py
```

You will be prompted to enter ASCII codes and see the translated key names immediately.

Example session:

```
Enter ASCII code: 49
Code 49: 1

Enter ASCII code: 165
Code 165: ENTER

Enter ASCII code: 177
Code 177: ESC
```

Type `exit` to quit the test program.

---

## License

Licensed under the Apache License 2.0 (matching ClockworkPi project conventions).

