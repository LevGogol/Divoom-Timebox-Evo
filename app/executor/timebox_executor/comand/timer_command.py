import socket
import threading
import time
import multiprocessing
from pathlib import Path
from app.draw_pixel import MAC_ADDRESS, RFCOMM_CHANNEL
from app.protocol import build_image_message
from playsound import playsound

SOUND_FILE = Path(__file__).resolve().parent.parent.parent.parent / "timer.mp3"

def display_progress(remaining: int, total: int, sock: socket.socket) -> None:
    fraction = remaining / total if total > 0 else 0
    filled = round(fraction * 256)
    if fraction > 0.5:
        color = (0, 255, 0)
    elif fraction > 0.25:
        color = (255, 255, 0)
    else:
        color = (255, 0, 0)
    pixels = [1 if i < filled else 0 for i in range(256)]
    sock.send(build_image_message(pixels, [(0, 0, 0), color]))

def clear_display(sock: socket.socket) -> None:
    sock.send(build_image_message([0] * 256, [(0, 0, 0)]))

def _play_sound_file(sound_path: str) -> None:
    playsound(sound_path)

class SoundPlayer:
    def __init__(self):
        self._process: multiprocessing.Process | None = None
        self._lock = threading.Lock()

    def play(self, sound_path: Path) -> None:
        self.stop()
        with self._lock:
            self._process = multiprocessing.Process(
                target=_play_sound_file,
                args=(str(sound_path),),
                daemon=True,
            )
            self._process.start()

    def stop(self) -> None:
        with self._lock:
            if self._process is None:
                return
            if self._process.is_alive():
                self._process.terminate()
                self._process.join(timeout=1)
            self._process = None

class TimerCommand(threading.Thread):
    def __init__(self, minutes: int, seconds: int = 0):
        super().__init__(daemon=True)
        self.total_seconds = max(0, minutes) * 60 + max(0, seconds)
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def execute(self):
        self.start()

    def run(self):
        sock = None
        sound_player = SoundPlayer()
        try:
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.settimeout(10)
            sock.connect((MAC_ADDRESS, RFCOMM_CHANNEL))
            sock.settimeout(None)
            remaining = self.total_seconds
            total = self.total_seconds
            while remaining > 0 and not self._stop.is_set():
                m = remaining // 60
                s = remaining % 60
                print(f"[Timer] {m:02d}:{s:02d}")
                display_progress(remaining, total, sock)
                time.sleep(1)
                remaining -= 1
            if not self._stop.is_set():
                print("[Timer] Время вышло!")
                display_progress(0, total, sock)
                time.sleep(0.5)
                if SOUND_FILE.exists():
                    try:
                        sound_player.play(SOUND_FILE)
                    except Exception as e:
                        print(f"Ошибка при проигрывании mp3: {e}")
                else:
                    print(f"Файл mp3 не найден: {SOUND_FILE}")
        except Exception as e:
            print(f"[TimerCommand] Ошибка: {e}")
        finally:
            if sock:
                try:
                    clear_display(sock)
                    sock.close()
                except Exception:
                    pass
            sound_player.stop()
