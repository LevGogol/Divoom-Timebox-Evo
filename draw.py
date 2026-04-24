"""Draw on a Divoom Timebox Evo — convenient wrapper.

Edit the pixel map below and run: python draw.py
"""

import socket
import time

from app.protocol import build_brightness_message, build_image_message
from app.draw_pixel import MAC_ADDRESS, RFCOMM_CHANNEL

# --- Edit here ---

BRIGHTNESS = 100

# 16x16 pixel grid. Use color names defined below.
# '.' = black (off), 'R' = red, 'G' = green, 'B' = blue, 'W' = white, etc.
COLORS = {
    ".": (0, 0, 0),
    "R": (255, 0, 0),
    "G": (0, 255, 0),
    "B": (0, 0, 255),
    "W": (255, 255, 255),
    "Y": (255, 255, 0),
    "C": (0, 255, 255),
    "M": (255, 0, 255),
    "O": (255, 128, 0),
}

GRID = [
    "BBBBBBBBBBBBBBBB",
    "................",
    "................",
    "................",
    "................",
    ".....RRRRRR.....",
    "....R......R....",
    "...R..G..G..R...",
    "...R........R...",
    "...R..R..R..R...",
    "...R...RR...R...",
    "....R......R....",
    ".....RRRRRR.....",
    "................",
    "................",
    "................",
]

# --- End edit ---


def parse_grid(grid, color_map):
    palette = []
    pixels = []
    for row in grid:
        for ch in row:
            color = color_map.get(ch, (0, 0, 0))
            if color not in palette:
                palette.append(color)
            pixels.append(palette.index(color))
    return pixels, palette


def main():
    if len(GRID) != 16 or any(len(row) != 16 for row in GRID):
        print("Error: GRID must be exactly 16 rows of 16 characters")
        return

    pixels, palette = parse_grid(GRID, COLORS)
    print(f"Palette: {len(palette)} colors")

    brightness_msg = build_brightness_message(BRIGHTNESS)
    image_msg = build_image_message(pixels, palette)

    print(f"Connecting to {MAC_ADDRESS}...")
    sock = socket.socket(
        socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
    )
    sock.settimeout(10)
    try:
        sock.connect((MAC_ADDRESS, RFCOMM_CHANNEL))
        print("Connected!")
        time.sleep(0.5)
        sock.send(brightness_msg)
        time.sleep(0.1)
        sock.send(image_msg)
        print("Done!")
        time.sleep(1)
    except OSError as e:
        print(f"Connection failed: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
