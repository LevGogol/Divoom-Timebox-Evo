"""Draw a single pixel on a Divoom Timebox Evo.

Usage:
    python draw_pixel.py [x] [y] [r] [g] [b]

Examples:
    python draw_pixel.py
    python draw_pixel.py 0 0 255 0 0
    python draw_pixel.py 8 8 0 255 0
"""

import socket
import sys
import time

from protocol import build_brightness_message, build_image_message

MAC_ADDRESS = "11:75:58:E7:62:84"
RFCOMM_CHANNEL = 1


def create_pixel_image(
    x: int, y: int, color: tuple[int, int, int] = (255, 0, 0)
) -> tuple[list[int], list[tuple[int, int, int]]]:
    """Create a 16x16 image with a single colored pixel on black background."""
    colors = [(0, 0, 0), color]
    pixels = [0] * 256
    pixels[x + 16 * y] = 1
    return pixels, colors


def main():
    x = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    y = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    r = int(sys.argv[3]) if len(sys.argv) > 3 else 255
    g = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    b = int(sys.argv[5]) if len(sys.argv) > 5 else 0

    if not (0 <= x <= 15 and 0 <= y <= 15):
        print("Error: x and y must be between 0 and 15")
        sys.exit(1)

    print(f"Pixel: ({x}, {y}), Color: ({r}, {g}, {b})")

    # Build messages
    brightness_msg = build_brightness_message(100)
    pixels, colors = create_pixel_image(x, y, (r, g, b))
    image_msg = build_image_message(pixels, colors)

    # Connect via Bluetooth RFCOMM
    print(f"Connecting to {MAC_ADDRESS} (RFCOMM channel {RFCOMM_CHANNEL})...")
    sock = socket.socket(
        socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
    )
    sock.settimeout(10)
    try:
        sock.connect((MAC_ADDRESS, RFCOMM_CHANNEL))
        print("Connected!")

        time.sleep(0.5)

        print("Setting brightness to 100%...")
        sock.send(brightness_msg)
        time.sleep(0.1)

        print("Sending pixel image...")
        sock.send(image_msg)

        print("Done! Check your Timebox Evo display.")
        time.sleep(1)
    except OSError as e:
        print(f"Connection failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure Timebox Evo is ON and in Bluetooth range")
        print("  2. Pair the device in Windows Bluetooth settings first")
        print("  3. Verify the MAC address is correct")
        print("  4. Try changing RFCOMM_CHANNEL to 2 in draw_pixel.py")
        sys.exit(1)
    finally:
        sock.close()


if __name__ == "__main__":
    main()
