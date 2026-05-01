from app.app import App
from app.commander.voice_commander import VoiceCommander
from app.executor.console_executor import ConsoleExecutor
from app.executor.timebox_executor.timebox_executor import TimeboxExecutor
from app.power import Power


def main() -> None:
    power = Power()
    console_executor = ConsoleExecutor()
    timebox_executor = TimeboxExecutor(console_executor, power)
    voice_commander = VoiceCommander(timebox_executor)
    App(voice_commander).run()


if __name__ == "__main__":
    main()
