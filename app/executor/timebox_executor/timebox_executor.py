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
        words = cmd.split()

        # Найти все индексы ключевых слов
        matches = []
        for i, word in enumerate(words):
            if word in self.WAKE_WORDS:
                matches.append((i, 'wakeup'))
            elif word == "яркость":
                matches.append((i, 'brightness'))

        if not matches:
            IgnoreCommand().execute()
            return

        # Выполнить только последнюю найденную команду
        idx, cmd_type = matches[-1]
        if cmd_type == 'wakeup':
            WakeupCommand().execute()
            return
        elif cmd_type == 'brightness':
            # Попробовать взять следующее слово как значение яркости
            if idx + 1 < len(words):
                value = self.parse_brightness(words[idx + 1])
                if value is not None:
                    BrightnessCommand(value).execute()
                    return
            IgnoreCommand().execute()
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
