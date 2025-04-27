# Conway's Game of Life - PicoCalc MicroPython Educational Demo
#
# Author: Daniel Gentleman (daniel@danielgentleman.com)
# License: Apache 2.0
#
# A simple implementation of Conway's Game of Life
# adapted for the ClockworkPi PicoCalc (RP2350 MCU)
# using MicroPython and a 16-color indexed display.
#
# Demonstrates: Screen drawing, keyboard input, timing control.

# ================== LICENSE ==================
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================

import picocalc
import random
import time

# === Settings ===
DEBUG = False  # Set True for verbose frame timing
CELL_SIZE = 6  # Recommended: 6 for balance (53x53 grid); must be >=4 on Pico 2 W H
GRID_PIXELS = 320
GRID_SIZE = GRID_PIXELS // CELL_SIZE

LIVE_CHANCE = 0.3  # 30% of cells alive initially

# Color mappings (16-color index)
COLORS = {
    0: 0,    # dead = black
    1: 9,    # bright red
    2: 10,   # bright green
    3: 12,   # bright blue
}

# === Initialize Display and Keyboard ===
display = picocalc.PicoDisplay(GRID_PIXELS, GRID_PIXELS)
keyboard = picocalc.PicoKeyboard()

# === Initialize Grid ===
def random_grid():
    return [[random.choice([1, 2, 3]) if random.random() < LIVE_CHANCE else 0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

grid = random_grid()

# === Game Update ===
def update():
    global grid
    if DEBUG:
        print(">>> START update()")

    start_update = time.ticks_ms()

    neighbor_counts = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if grid[y][x] != 0:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx = (x + dx) % GRID_SIZE
                        ny = (y + dy) % GRID_SIZE
                        neighbor_counts[ny][nx] += 1

    new_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            neighbors = neighbor_counts[y][x]
            if grid[y][x] != 0:
                if neighbors in (2, 3):
                    new_grid[y][x] = grid[y][x]  # Stay alive
            else:
                if neighbors == 3:
                    color = pick_birth_color(x, y)
                    new_grid[y][x] = color

    grid[:] = new_grid

    end_update = time.ticks_ms()
    if DEBUG:
        print(f"<<< FINISH update() - Time: {end_update - start_update} ms")

def pick_birth_color(x, y):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx = (x + dx) % GRID_SIZE
            ny = (y + dy) % GRID_SIZE
            if grid[ny][nx] != 0:
                return grid[ny][nx]
    return random.choice([1, 2, 3])

# === Drawing ===
def draw():
    if DEBUG:
        print(">>> START draw()")

    start_draw = time.ticks_ms()

    display.fill(0)
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            color = COLORS.get(grid[y][x], 0)
            display.fill_rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE, color)
    display.show()

    end_draw = time.ticks_ms()
    if DEBUG:
        print(f"<<< FINISH draw() - Time: {end_draw - start_draw} ms")

# === Main Loop ===

print("Pico Life v1.0 - Arrows = Speed Control, R = Reset, Q = Quit")
print("Initializing... please wait 5 seconds.")

running = True
speed = 0.01  # Start fast
start_time = time.ticks_ms()

# Drain startup junk
_ = keyboard.keyEvent()

while running:
    event = keyboard.keyEvent()
    if event:
        if time.ticks_diff(time.ticks_ms(), start_time) > 5000:  # Ignore keys for first 5s
            if event[0] == 1:
                if 32 <= event[1] <= 126:
                    keycode = chr(event[1])
                    if keycode == 'q':
                        running = False
                    elif keycode == 'r':
                        grid = random_grid()
                else:
                    if event[1] == 180:  # Left Arrow
                        speed = min(speed + 0.01, 0.2)
                    elif event[1] == 183:  # Right Arrow
                        speed = max(speed - 0.01, 0.001)

    draw()
    update()
    time.sleep(speed)

# Clean exit
display.fill(0)
display.show()
print("Program ended. Back to REPL.")
time.sleep(1)
