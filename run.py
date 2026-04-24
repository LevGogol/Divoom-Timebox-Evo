from app.app import App
from app.commander.voice_commander import VoiceCommander
from app.executor.timebox_executor.timebox_executor import TimeboxExecutor
from app.executor.console_executor import ConsoleExecutor



def main() -> None:
    console_executor = ConsoleExecutor()
    timebox_executor = TimeboxExecutor(console_executor)
    voice_commander = VoiceCommander(timebox_executor)
    App(voice_commander).run()

if __name__ == "__main__":
    main()
