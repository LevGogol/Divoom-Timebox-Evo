from app.commander import Commander
from app.executor import Executor


class App:
    def __init__(self, commander: Commander, executor: Executor) -> None:
        self._commander = commander
        self._executor = executor

    def run(self) -> None:
        try:
            while True:
                command = self._commander.next_command()
                if command:
                    self._executor.execute(command)
        except KeyboardInterrupt:
            print("\nStopped.")
