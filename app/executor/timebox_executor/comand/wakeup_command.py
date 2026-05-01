import socket
import threading
import time

from app.draw_pixel import MAC_ADDRESS, RFCOMM_CHANNEL
from app.protocol import build_brightness_message, build_image_message

_SMILEY_GRID = [
    "................",
    "................",
    ".....YYYYYY.....",
    "...YYYYYYYYYY...",
    "..YYYYYYYYYYYY..",
    "..YY........YY..",
    ".YY...Y..Y...YY.",
    ".YY...Y..Y...YY.",
    ".YY..........YY.",
    ".YY.Y......Y.YY.",
    ".YY..YYYYYY..YY.",
    "..YY........YY..",
    "..YYYYYYYYYYYY..",
    "...YYYYYYYYYY...",
    ".....YYYYYY.....",
    "................",
]
_SMILEY_COLORS = {".": (0, 0, 0), "Y": (255, 220, 0)}

def display_smiley(sock: socket.socket) -> None:
    palette = []
    pixels = []
    for row in _SMILEY_GRID:
        for ch in row:
            color = _SMILEY_COLORS.get(ch, (0, 0, 0))
            if color not in palette:
                palette.append(color)
            pixels.append(palette.index(color))
    sock.send(build_image_message(pixels, palette))

def _run():
    try:
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.settimeout(10)
        sock.connect((MAC_ADDRESS, RFCOMM_CHANNEL))
        time.sleep(0.1)
        display_smiley(sock)
    except Exception as e:
        print(f"[WakeupCommand] Ошибка: {e}")
    finally:
        try:
            sock.close()
        except Exception:
            pass

class WakeupCommand:
    def execute(self):
        threading.Thread(target=_run, daemon=True).start()
