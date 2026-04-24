from app.app import App
from app.commander.voice_commander import VoiceCommander
from app.executor.console_executor import ConsoleExecutor
from app.executor.timebox_executor.timebox_executor import TimeboxExecutor


def main() -> None:
    App(VoiceCommander(), TimeboxExecutor(ConsoleExecutor())).run()


if __name__ == "__main__":
    main()
