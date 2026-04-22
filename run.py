from app.app import App
from app.commander.terminal_commander import TerminalCommander
from app.executor import TimeboxExecutor



def main() -> None:
    App(TerminalCommander(), TimeboxExecutor()).run()


if __name__ == "__main__":
    main()
