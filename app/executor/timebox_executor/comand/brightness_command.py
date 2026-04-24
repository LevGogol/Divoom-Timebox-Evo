import socket
import time
from app.draw_pixel import MAC_ADDRESS, RFCOMM_CHANNEL
from app.protocol import build_brightness_message

class BrightnessCommand:
    def __init__(self, brightness: int = 100):
        self.brightness = max(0, min(100, brightness))

    def execute(self):
        try:
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.settimeout(10)
            sock.connect((MAC_ADDRESS, RFCOMM_CHANNEL))
            time.sleep(0.5)
            sock.send(build_brightness_message(self.brightness))
            time.sleep(0.1)
        except Exception as e:
            print(f"[BrightnessCommand] Ошибка: {e}")
        finally:
            try:
                sock.close()
            except Exception:
                pass
