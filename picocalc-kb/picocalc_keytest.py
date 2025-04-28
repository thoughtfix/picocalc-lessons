# test_keymap.py
import picocalc_keymap

def test_loop():
    print("PicoCalc Keymap Test: Type an ASCII code to look up its meaning. Type 'exit' to quit.")
    while True:
        entry = input("Enter ASCII code: ").strip()
        if entry.lower() == 'exit':
            break
        try:
            code = int(entry)
            key_name = picocalc_keymap.get_key_name(code)
            print(f"Code {code}: {key_name}")
        except ValueError:
            print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    test_loop()

