"""Voice control for Divoom Timebox Evo.

Wake word: "алиса" (or "дивум")
After wake word, say a color: красный, зелёный, синий, белый, жёлтый...

Requirements:
    pip install vosk pyaudio

Russian model (~45MB), download once:
    https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
    Extract so that this folder exists: vosk-model-small-ru-0.22/
"""

import json
import queue
import socket
import sys
import time

import pyaudio
from vosk import KaldiRecognizer, Model

from draw_pixel import MAC_ADDRESS, RFCOMM_CHANNEL
from protocol import build_brightness_message, build_image_message

WAKE_WORDS = {"коробка", "колонка"}

COLORS = {
    "красный":    (255, 0,   0),
    "красного":   (255, 0,   0),
    "зелёный":    (0,   255, 0),
    "зелёного":   (0,   255, 0),
    "синий":      (0,   0,   255),
    "синего":     (0,   0,   255),
    "белый":      (255, 255, 255),
    "белого":     (255, 255, 255),
    "жёлтый":     (255, 255, 0),
    "жёлтого":    (255, 255, 0),
    "оранжевый":  (255, 128, 0),
    "фиолетовый": (128, 0,   255),
    "голубой":    (0,   255, 255),
    "выключи":    (0,   0,   0),
    "выключить":  (0,   0,   0),
    "чёрный":     (0,   0,   0),
}

MODEL_PATH = "vosk-model-small-ru-0.22"
SAMPLE_RATE = 16000
WAKE_TIMEOUT = 5  # seconds to wait for color after wake word


def fill_screen(color: tuple[int, int, int], sock: socket.socket) -> None:
    pixels = [0] * 256
    msg = build_image_message(pixels, [color])
    sock.send(msg)


def connect() -> socket.socket:
    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    sock.settimeout(10)
    sock.connect((MAC_ADDRESS, RFCOMM_CHANNEL))
    sock.settimeout(None)
    return sock


def main():
    print(f"Loading model from '{MODEL_PATH}'...")
    try:
        model = Model(MODEL_PATH)
    except Exception:
        print(f"Model not found!\n")
        print("Download the Russian model:")
        print("  https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip")
        print(f"  Extract so that folder '{MODEL_PATH}/' is next to this script.")
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

    wake_words_str = " / ".join(WAKE_WORDS)
    colors_str = ", ".join(sorted({w for w in COLORS if not w.endswith("го")}))
    print(f"\nListening... Wake word: {wake_words_str}")
    print(f"Colors: {colors_str}")
    print("Ctrl+C to stop\n")

    wake_time: float | None = None

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

            # Detected wake word
            if word_set & WAKE_WORDS:
                wake_time = time.time()
                print(f"[Wake] '{text}' → жду цвет...")

            # Timed out
            if wake_time is not None and time.time() - wake_time > WAKE_TIMEOUT:
                print("[Timeout] цвет не услышан, засыпаю.")
                wake_time = None

            # Detect color (wake word and color can be in same phrase)
            if wake_time is not None:
                for word in words:
                    if word in COLORS:
                        color = COLORS[word]
                        print(f"[Color] '{word}' → RGB{color}")
                        try:
                            fill_screen(color, sock)
                        except OSError:
                            print("Соединение потеряно, переподключаюсь...")
                            sock = connect()
                            fill_screen(color, sock)
                        wake_time = None
                        break

    except KeyboardInterrupt:
        print("\nОстановлено.")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        sock.close()


if __name__ == "__main__":
    main()