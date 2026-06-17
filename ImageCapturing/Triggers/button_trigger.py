from ImageCapturing.Triggers.abstract_trigger import Abstract_Trigger

class ButtonTrigger(Abstract_Trigger):

    def __init__(self):
        super().__init__()

    def triggerLoop(self):
        while True:
            input("Press enter to capture...")
            super().notifyAllObservers()