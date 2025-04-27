# snake.py
# Snake for PicoCalc (Pico 2 W H installed)
#
# Author: Daniel Gentleman (code@danielgentleman.com)
# License: Apache 2.0
#
# A simple Snake clone demonstrating input, graphics, scorekeeping, and restart behavior.
# Intended audience: People who want to code for the PicoCalc and just need some examples.

import picocalc
import random
import time

# === Settings ===
DEBUG = False
CELL_SIZE = 6  # Snake segment size (in pixels)
GRID_PIXELS = 320
GRID_SIZE = GRID_PIXELS // CELL_SIZE

SNAKE_COLOR = 10  # Bright green
APPLE_COLOR = 9   # Bright red
SCORE_COLOR = 15  # Bright white

START_SPEED = 0.1  # Seconds per move. TODO: Let players specify this.

# === Initialize Display and Keyboard ===
display = picocalc.PicoDisplay(GRID_PIXELS, GRID_PIXELS)
keyboard = picocalc.PicoKeyboard()

# === Game State ===
snake = [(GRID_SIZE // 2, GRID_SIZE // 2)]  # Snake starts center
direction = (0, -1)  # Start moving upward
apple = None
score = 0
speed = START_SPEED
running = True
game_over = False

# === Functions ===

def place_apple():
    while True:
        x = random.randint(0, GRID_SIZE - 1)
        y = random.randint(0, GRID_SIZE - 1)
        if (x, y) not in snake:
            return (x, y)

def draw():
    display.fill(0)

    # Draw snake
    for (x, y) in snake:
        display.fill_rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE, SNAKE_COLOR)

    # Draw apple
    if apple:
        ax, ay = apple
        display.fill_rect(ax * CELL_SIZE, ay * CELL_SIZE, CELL_SIZE, CELL_SIZE, APPLE_COLOR)

    # Draw score
    display.text(f"Score: {score}", 2, 2, SCORE_COLOR)

    display.show()

def move_snake():
    global snake, apple, score, speed, game_over

    head_x, head_y = snake[0]
    new_x = (head_x + direction[0]) % GRID_SIZE
    new_y = (head_y + direction[1]) % GRID_SIZE
    new_head = (new_x, new_y)

    # Check collision with self
    if new_head in snake:
        game_over = True
        return

    snake = [new_head] + snake

    # Check apple
    if apple and new_head == apple: # NOM NOM NOM NOM NOM
        score += 1
        apple_spawn()
        # Optional: speed up slightly every apple
        # speed = max(0.05, speed - 0.005)
    else:
        snake.pop()  # Move forward, remove tail

def apple_spawn():
    global apple
    apple = place_apple()

def handle_input():
    global direction, running, game_over

    event = keyboard.keyEvent()
    if event:
        if event[0] == 1:  # Key pressed
            if 32 <= event[1] <= 126:
                if game_over:
                    reset_game()
            else:
                if event[1] == 180:  # Left
                    if direction != (1, 0):
                        direction = (-1, 0)
                elif event[1] == 183:  # Right
                    if direction != (-1, 0):
                        direction = (1, 0)
                elif event[1] == 181:  # Up
                    if direction != (0, 1):
                        direction = (0, -1)
                elif event[1] == 182:  # Down
                    if direction != (0, -1):
                        direction = (0, 1)

def reset_game():
    global snake, direction, apple, score, speed, game_over

    snake = [(GRID_SIZE // 2, GRID_SIZE // 2)]
    direction = (0, -1)
    apple = place_apple()
    score = 0
    speed = START_SPEED
    game_over = False

def draw_game_over():
    display.fill(0)
    display.text("GAME OVER!", 100, 120, SCORE_COLOR)
    display.text(f"Score: {score}", 110, 140, SCORE_COLOR)
    display.text("Press any key...", 70, 170, SCORE_COLOR)
    display.show()

# === Main Loop ===

print("Pico Snake v1.0 - Arrows = Move, Any Key = Restart")

apple_spawn()
reset_game()

last_move = time.ticks_ms()

while running:
    handle_input()

    now = time.ticks_ms()
    if time.ticks_diff(now, last_move) > int(speed * 1000):
        if not game_over:
            move_snake()
            draw()
        else:
            draw_game_over()
        last_move = now

    time.sleep(0.01)

# Clean exit
display.fill(0)
display.show()
print("Program ended.")

