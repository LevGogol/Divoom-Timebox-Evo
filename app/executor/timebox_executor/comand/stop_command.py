import socket

from app.draw_pixel import MAC_ADDRESS, RFCOMM_CHANNEL
from app.protocol import build_clock_message


class StopCommand:
    def __init__(self, stoppable=None):
        self.stoppable = stoppable

    def execute(self):
        if self.stoppable is not None:
            self.stoppable.stop()
            self.stoppable.join()
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.settimeout(10)
        try:
            sock.connect((MAC_ADDRESS, RFCOMM_CHANNEL))
            sock.send(build_clock_message())
        except Exception as e:
            print(f"[StopCommand] Ошибка: {e}")
        finally:
            sock.close()
