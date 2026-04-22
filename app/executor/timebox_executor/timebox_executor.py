from app.executor import Executor
from app.executor.timebox_executor.wakeup import wakeup
from app.executor.timebox_executor.ignore import ignore

class TimeboxExecutor:
    def __init__(self):
        self._commands = {
            "wakeup": wakeup,
        }

    def execute(self, command: str) -> None:
        func = self._commands.get(command, ignore)
        func()
