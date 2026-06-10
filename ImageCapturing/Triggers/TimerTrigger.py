from ImageCapturing.Triggers.AbstractTrigger import Abstract_Trigger
import time

class TimerTrigger(Abstract_Trigger):

    def __init__(self, timeSeconds):
        super().__init__()
        self.timeSeconds = timeSeconds

    def triggerLoop(self):
        while True:
            timeBegin = time.time()

            super().notifyAllObservers()

            timeEnd = time.time()
            timeElapsed = timeEnd - timeBegin
            time.sleep(self.timeSeconds-timeElapsed)