from typing import Protocol


class Executor(Protocol):
    def execute(self, command: str) -> None: ...
