from app.executor import Executor
from app.executor.timebox_executor import wakeup

class TimeboxExecutor:
    def __init__(self):
        self._commands = {
            "wakeup": wakeup,
        }

    def execute(self, command: str) -> None:
        func = self._commands.get(command)
        if func:
            func()
        else:
            print(f"[unknown command] {command}")
