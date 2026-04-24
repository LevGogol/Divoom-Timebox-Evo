import queue
import threading
import json
from vosk import Model, KaldiRecognizer
import pyaudio
from pathlib import Path

MODEL_PATH = Path("vosk-model-small-ru-0.22")
SAMPLE_RATE = 16000



from app.executor.timebox_executor.timebox_executor import TimeboxExecutor
from app.executor.console_executor import ConsoleExecutor

class VoiceCommander:
    def __init__(self, executor, model_path=MODEL_PATH, sample_rate=SAMPLE_RATE):
        self._queue: queue.Queue[str] = queue.Queue()
        self._model_path = model_path
        self._sample_rate = sample_rate
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        self._executor = executor



    def next_command(self) -> str:
        last_command = getattr(self, '_last_command', None)
        while not self._stop_event.is_set():
            try:
                command = self._queue.get(timeout=0.1)
                if command and command != last_command:
                    self._executor.execute(command)
                    self._last_command = command
                    return command
                else:
                    continue
            except queue.Empty:
                continue
            except KeyboardInterrupt:
                self._stop_event.set()
                raise

    def _listen(self):
        print(f"[VoiceCommander] Loading model from '{self._model_path}'...")
        model = Model(str(self._model_path))
        rec = KaldiRecognizer(model, self._sample_rate)
        pa = pyaudio.PyAudio()
        audio_queue: queue.Queue[bytes] = queue.Queue()

        def audio_callback(in_data, frame_count, time_info, status):
            audio_queue.put(in_data)
            return (None, pyaudio.paContinue)

        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._sample_rate,
            input=True,
            frames_per_buffer=4000,
            stream_callback=audio_callback,
        )
        print("[VoiceCommander] Listening for any words...")
        try:
            while not self._stop_event.is_set():
                try:
                    data = audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                if rec.AcceptWaveform(data):
                    text = json.loads(rec.Result()).get("text", "").lower()
                else:
                    text = json.loads(rec.PartialResult()).get("partial", "").lower()
                if text:
                    self._queue.put(text)
        except Exception as e:
            print(f"[VoiceCommander] Error: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()
