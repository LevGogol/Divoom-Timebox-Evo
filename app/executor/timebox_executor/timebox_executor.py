from app.executor.timebox_executor.comand.ignore_command import IgnoreCommand
from app.executor.timebox_executor.comand.wakeup_command import WakeupCommand
from app.executor.timebox_executor.comand.brightness_command import BrightnessCommand

class FakeExecutor:
    def execute(self, command: str) -> None:
        pass

class TimeboxExecutor:
    WAKE_WORDS = {"коробка", "колонка"}

    def __init__(self, console_executor=None):
        if console_executor is None:
            console_executor = FakeExecutor()
        self._console_executor = console_executor

    def execute(self, command: str) -> None:
        self._console_executor.execute(command)
        cmd = command.strip().lower()
        if cmd in self.WAKE_WORDS:
            WakeupCommand().execute()
            return

        if cmd.startswith("яркость"):
            parts = cmd.split()
            if len(parts) == 2:
                value = self.parse_brightness(parts[1])
                if value is not None:
                    BrightnessCommand(value).execute()
                    return

        IgnoreCommand().execute()
    _WORDS_TO_NUM = {
        "ноль": 0, "один": 1, "одна": 1, "одну": 1, "два": 2, "две": 2, "три": 3, "четыре": 4, "пять": 5,
        "шесть": 6, "семь": 7, "восемь": 8, "девять": 9, "десять": 10, "одиннадцать": 11, "двенадцать": 12,
        "тринадцать": 13, "четырнадцать": 14, "пятнадцать": 15, "шестнадцать": 16, "семнадцать": 17,
        "восемнадцать": 18, "девятнадцать": 19, "двадцать": 20, "тридцать": 30, "сорок": 40, "пятьдесят": 50,
        "шестьдесят": 60, "семьдесят": 70, "восемьдесят": 80, "девяносто": 90, "сто": 100
    }

    @classmethod
    def parse_brightness(cls, word: str) -> int | None:
        if word.isdigit():
            return int(word)
        if word in cls._WORDS_TO_NUM:
            return cls._WORDS_TO_NUM[word]
        parts = word.split("-")
        if len(parts) == 2 and all(p in cls._WORDS_TO_NUM for p in parts):
            return cls._WORDS_TO_NUM[parts[0]] + cls._WORDS_TO_NUM[parts[1]]
        return None
