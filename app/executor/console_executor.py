from .timebox_executor.timebox_executor import TimeboxExecutor

class ConsoleExecutor:
    def __init__(self):
        pass

    def execute(self, command: str) -> None:
        print(f"[exec] {command}")
