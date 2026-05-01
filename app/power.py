import atexit
import contextlib
import signal
import sys

from app.executor.timebox_executor.comand.brightness_command import BrightnessCommand
from app.power_monitor import WindowsPowerMonitor


class Power:
    def on(self) -> None:
        BrightnessCommand(100).execute()

    def off(self) -> None:
        BrightnessCommand(0).execute()

    def set(self, value: int) -> None:
        BrightnessCommand(value).execute()

    def start(self) -> None:
        self.on()
        atexit.register(self.off)

        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
        with contextlib.suppress(AttributeError):
            signal.signal(signal.SIGBREAK, lambda *_: sys.exit(0))

        WindowsPowerMonitor(on_suspend=self.off, on_resume=self.on)
