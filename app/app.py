from app.commander import Commander
from app.executor import Executor


class App:
    def __init__(self, commander: Commander) -> None:
        self._commander = commander

    def run(self) -> None:
        try:
            while True:
                self._commander.next_command()
        except KeyboardInterrupt:
            print("\nStopped.")
