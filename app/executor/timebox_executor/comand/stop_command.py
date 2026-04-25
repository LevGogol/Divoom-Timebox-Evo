class StopCommand:
    def __init__(self, stoppable):
        self.stoppable = stoppable

    def execute(self):
        self.stoppable.stop()
