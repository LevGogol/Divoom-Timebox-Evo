from app.executor.timebox_executor.comand.ignore_command import IgnoreCommand
from app.executor.timebox_executor.comand.stop_command import StopCommand
from app.executor.timebox_executor.comand.timer_command import TimerCommand
from app.executor.timebox_executor.comand.wakeup_command import WakeupCommand


class FakeExecutor:
    def execute(self, command: str) -> None:
        pass

class TimeboxExecutor:

    WAKE_WORDS = {"коробка", "колонка"}

    def _parse_number(self, words: list[str]) -> tuple[int, int]:
        total = 0
        i = 0
        if i < len(words) and words[i] in self._WORDS_TO_NUM:
            total += self._WORDS_TO_NUM[words[i]]
            i += 1
        if i < len(words) and words[i] in self._WORDS_TO_NUM:
            total += self._WORDS_TO_NUM[words[i]]
            i += 1
        return total, i

    def __init__(self, console_executor=None, power=None):
        if console_executor is None:
            console_executor = FakeExecutor()
        self._console_executor = console_executor
        self._power = power
        self._active_timer = None
        if power is not None:
            power.start()

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
            elif word == "таймер":
                matches.append((i, 'timer'))
            elif word == "стоп":
                matches.append((i, 'stop'))

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
            if idx + 1 < len(words) and self._power is not None:
                value = self.parse_brightness(words[idx + 1])
                if value is not None:
                    self._power.set(value)
                    return
            IgnoreCommand().execute()
            return
        elif cmd_type == 'timer':
            # Попробовать взять следующее слово как число, затем единицу измерения
            if idx + 1 < len(words):
                minutes, seconds = self.parse_timer(words[idx+1:])
                if minutes is not None:
                    if self._active_timer:
                        self._active_timer.stop()
                    timer = TimerCommand(minutes, seconds)
                    self._active_timer = timer
                    timer.execute()
                    return
            IgnoreCommand().execute()
            return
        elif cmd_type == 'stop':
            if self._active_timer:
                StopCommand(self._active_timer).execute()
                self._active_timer = None
            else:
                StopCommand().execute()
            return
        IgnoreCommand().execute()

    def parse_timer(self, words: list[str]) -> tuple[int|None, int]:
        # Пример: ['на', 'пять', 'минут'] или ['тридцать', 'секунд']
        # Удаляем 'на', если есть
        if words and words[0] == 'на':
            words = words[1:]
        # Парсим число
        num, consumed = self._parse_number(words)
        if num == 0 or consumed == 0:
            return None, 0
        rest = words[consumed:]
        if not rest:
            return None, 0
        unit = rest[0]
        if unit in ("минута", "минуту", "минуты", "минут"):
            return num, 0
        if unit in ("секунда", "секунду", "секунды", "секунд"):
            return num // 60, num % 60
        return None, 0

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
