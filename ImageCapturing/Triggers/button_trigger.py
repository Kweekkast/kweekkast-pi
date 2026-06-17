from ImageCapturing.Triggers.abstract_trigger import AbstractTrigger

class ButtonTrigger(AbstractTrigger):

    def __init__(self):
        super().__init__()

    def triggerLoop(self):
        while True:
            input("Press enter to capture...")
            super().notifyAllObservers()