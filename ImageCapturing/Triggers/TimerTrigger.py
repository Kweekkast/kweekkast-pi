from ImageCapturing.Triggers.AbstractTrigger import Abstract_Trigger
import StringGenerators
import time

class TimerTrigger(Abstract_Trigger):

    def __init__(self, timeSeconds):
        super().__init__()
        self.timeSeconds = timeSeconds

    def triggerLoop(self):
        print(StringGenerators.fetchCustomDateString() + ": Timer Trigger: The triggerloop has started")
        while True:
            timeBegin = time.time()

            super().notifyAllObservers()

            timeEnd = time.time()
            timeElapsed = timeEnd - timeBegin
            if timeElapsed > self.timeSeconds:
                timeElapsed = self.timeSeconds
            time.sleep(self.timeSeconds-timeElapsed)