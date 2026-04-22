from typing import Protocol


class Commander(Protocol):
    def next_command(self) -> str: ...
