class TerminalCommander:
    def next_command(self) -> str:
        try:
            return input("> ").strip()
        except EOFError:
            raise KeyboardInterrupt
