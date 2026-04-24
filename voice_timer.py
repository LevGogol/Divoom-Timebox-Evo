"""Voice timer with visual countdown and alarm sound.

Say: "колонка, таймер на пять минут" / "таймер тридцать секунд"

Requirements: pip install vosk pyaudio playsound==1.2.2
Model: https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
Sound: Place timer.mp3 in the project root
"""

import json
import multiprocessing
import queue
import socket
import sys
import threading
import time
from pathlib import Path

import pyaudio
from playsound import playsound
from vosk import KaldiRecognizer, Model

from app.draw_pixel import MAC_ADDRESS, RFCOMM_CHANNEL
from app.protocol import build_brightness_message, build_image_message

WAKE_WORDS = {"коробка", "колонка"}
STOP_WORDS = {"стоп", "останови", "остановить"}
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "vosk-model-small-ru-0.22"
SAMPLE_RATE = 16000
WAKE_TIMEOUT = 8
SOUND_FILE = BASE_DIR / "timer.mp3"

_ONES = {
    "один": 1, "одну": 1, "одна": 1, "два": 2, "две": 2, "три": 3,
    "четыре": 4, "пять": 5, "шесть": 6, "семь": 7, "восемь": 8,
    "девять": 9, "десять": 10, "одиннадцать": 11, "двенадцать": 12,
    "тринадцать": 13, "четырнадцать": 14, "пятнадцать": 15,
    "шестнадцать": 16, "семнадцать": 17, "восемнадцать": 18, "девятнадцать": 19,
}
_TENS = {
    "двадцать": 20, "тридцать": 30, "сорок": 40,
    "пятьдесят": 50, "шестьдесят": 60,
}


def parse_number(words: list[str]) -> tuple[int, int]:
    """Return (value, words_consumed) from Russian number words."""
    total = 0
    i = 0
    if i < len(words) and words[i] in _TENS:
        total += _TENS[words[i]]
        i += 1
    if i < len(words) and words[i] in _ONES:
        total += _ONES[words[i]]
        i += 1
    return total, i


def parse_timer(words: list[str]) -> tuple[int, int] | None:
    """Parse 'таймер [на] N минут/секунд' → (minutes, seconds), or None."""
    try:
        idx = words.index("таймер")
    except ValueError:
        return None

    rest = words[idx + 1:]
    if rest and rest[0] == "на":
        rest = rest[1:]

    num, consumed = parse_number(rest)
    if num == 0 or consumed == 0:
        return None

    rest = rest[consumed:]
    if not rest:
        return None

    unit = rest[0]
    if unit in ("минута", "минуту", "минуты", "минут"):
        return (num, 0)
    if unit in ("секунда", "секунду", "секунды", "секунд"):
        return (num // 60, num % 60)
    return None


def connect(retries: int = 10, delay: float = 10.0) -> socket.socket:
    for attempt in range(1, retries + 1):
        try:
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.settimeout(10)
            sock.connect((MAC_ADDRESS, RFCOMM_CHANNEL))
            sock.settimeout(None)
            return sock
        except OSError as e:
            print(f"Connection attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
    raise OSError(f"Could not connect to {MAC_ADDRESS} after {retries} attempts")


def display_progress(remaining: int, total: int, sock: socket.socket) -> None:
    """Show progress bar: green filled, black empty."""
    fraction = remaining / total
    filled = round(fraction * 256)

    if fraction > 0.5:
        color = (0, 255, 0)  # Green
    elif fraction > 0.25:
        color = (255, 255, 0)  # Yellow
    else:
        color = (255, 0, 0)  # Red

    pixels = [1 if i < filled else 0 for i in range(256)]
    sock.send(build_image_message(pixels, [(0, 0, 0), color]))


def clear_display(sock: socket.socket) -> None:
    """Clear the Timebox screen."""
    sock.send(build_image_message([0] * 256, [(0, 0, 0)]))


_SMILEY_GRID = [
    "................",
    "................",
    ".....YYYYYY.....",
    "...YYYYYYYYYY...",
    "..YYYYYYYYYYYY..",
    "..YY........YY..",
    ".YY....YY....YY.",
    ".YY....YY....YY.",
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
    """Show a yellow smiley face on the Timebox screen."""
    palette: list[tuple[int, int, int]] = []
    pixels: list[int] = []
    for row in _SMILEY_GRID:
        for ch in row:
            color = _SMILEY_COLORS.get(ch, (0, 0, 0))
            if color not in palette:
                palette.append(color)
            pixels.append(palette.index(color))
    sock.send(build_image_message(pixels, palette))


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


class TimerThread(threading.Thread):
    def __init__(self, minutes: int, seconds: int, sock: socket.socket, sound_player: SoundPlayer):
        super().__init__(daemon=True)
        self.total_seconds = minutes * 60 + seconds
        self.sock = sock
        self.sound_player = sound_player
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        remaining = self.total_seconds
        while remaining > 0 and not self._stop.is_set():
            m = remaining // 60
            s = remaining % 60
            print(f"[Timer] {m:02d}:{s:02d}")
            display_progress(remaining, self.total_seconds, self.sock)
            time.sleep(1)
            remaining -= 1

        if not self._stop.is_set():
            print("[Timer] Время вышло!")
            display_progress(0, self.total_seconds, self.sock)
            time.sleep(0.5)

            if SOUND_FILE.exists():
                try:
                    self.sound_player.play(SOUND_FILE)
                except Exception as e:
                    print(f"Ошибка при проигрывании mp3: {e}")
            else:
                print(f"Файл mp3 не найден: {SOUND_FILE}")


def main():
    print(f"Loading model from '{MODEL_PATH}'...")
    try:
        model = Model(str(MODEL_PATH))
    except Exception:
        print("Model not found!")
        print("Download: https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip")
        print(f"Extract folder '{MODEL_PATH}/' next to this script.")
        sys.exit(1)

    print(f"Connecting to Divoom {MAC_ADDRESS}...")
    try:
        sock = connect()
    except OSError as e:
        print(f"Bluetooth connection failed: {e}")
        sys.exit(1)
    print("Connected!")
    sock.send(build_brightness_message(100))
    time.sleep(0.1)

    rec = KaldiRecognizer(model, SAMPLE_RATE)
    audio_queue: queue.Queue[bytes] = queue.Queue()

    def audio_callback(in_data, frame_count, time_info, status):
        audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=4000,
        stream_callback=audio_callback,
    )

    print(f"\nListening... Wake words: {', '.join(WAKE_WORDS)}")
    print('Пример: "колонка, таймер на пять минут"')
    print("Ctrl+C to stop\n")

    wake_time: float | None = None
    active_timer: TimerThread | None = None
    sound_player = SoundPlayer()

    try:
        while True:
            data = audio_queue.get()

            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get("text", "").lower()
            else:
                text = json.loads(rec.PartialResult()).get("partial", "").lower()

            if not text:
                continue

            words = text.split()
            word_set = set(words)

            if word_set & STOP_WORDS:
                print(f"[Stop] '{text}'")
                if active_timer:
                    active_timer.stop()
                    active_timer = None
                sound_player.stop()
                clear_display(sock)
                wake_time = None
                continue

            if word_set & WAKE_WORDS:
                wake_time = time.time()
                print(f"[Wake] '{text}' → жду команду...")
                display_smiley(sock)

            if wake_time is not None and time.time() - wake_time > WAKE_TIMEOUT:
                print("[Timeout] команда не услышана, засыпаю.")
                wake_time = None

            if wake_time is not None:
                result = parse_timer(words)
                if result:
                    minutes, seconds = result
                    print(f"[Timer] Запускаю таймер на {minutes}м {seconds}с.")
                    if active_timer:
                        active_timer.stop()
                    sound_player.stop()
                    active_timer = TimerThread(minutes, seconds, sock, sound_player)
                    active_timer.start()
                    wake_time = None

    except KeyboardInterrupt:
        print("\nОстановлено.")
    finally:
        if active_timer:
            active_timer.stop()
        sound_player.stop()
        stream.stop_stream()
        stream.close()
        pa.terminate()
        sock.close()


if __name__ == "__main__":
    main()