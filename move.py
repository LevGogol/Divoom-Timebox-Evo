"""Move a white pixel on the Timebox Evo with WASD keys.

W = up, S = down, A = left, D = right, Q = quit
"""

import msvcrt
import socket
import time

from protocol import build_brightness_message, build_image_message
from draw_pixel import MAC_ADDRESS, RFCOMM_CHANNEL


def build_frame(x: int, y: int) -> bytes:
    colors = [(0, 0, 0), (255, 255, 255)]
    pixels = [0] * 256
    pixels[x + 16 * y] = 1
    return build_image_message(pixels, colors)


def main():
    x, y = 8, 8

    print(f"Connecting to {MAC_ADDRESS}...")
    sock = socket.socket(
        socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
    )
    sock.settimeout(10)
    try:
        sock.connect((MAC_ADDRESS, RFCOMM_CHANNEL))
    except OSError as e:
        print(f"Connection failed: {e}")
        return
    print("Connected!")

    time.sleep(0.5)
    sock.send(build_brightness_message(100))
    time.sleep(0.1)
    sock.send(build_frame(x, y))

    print(f"Position: ({x}, {y})")
    print("WASD to move, Q to quit")

    try:
        while True:
            key = msvcrt.getch().lower()
            moved = False

            if key == b"w" and y > 0:
                y -= 1
                moved = True
            elif key == b"s" and y < 15:
                y += 1
                moved = True
            elif key == b"a" and x > 0:
                x -= 1
                moved = True
            elif key == b"d" and x < 15:
                x += 1
                moved = True
            elif key == b"q":
                print("Bye!")
                break

            if moved:
                sock.send(build_frame(x, y))
                print(f"Position: ({x}, {y})")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
