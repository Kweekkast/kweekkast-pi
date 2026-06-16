from ImageCapturing.Triggers.AbstractTrigger import Abstract_Trigger
from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger
from LoggerComponent.LoggerEnum import MessageSeverity
import time

class TimerTrigger(Abstract_Trigger):

    def __init__(self, timeSeconds):
        super().__init__()
        self.timeSeconds = timeSeconds

    def triggerLoop(self):
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"The triggerloop has started")
        while True:
            timeBegin = time.time()

            super().notifyAllObservers()

            timeEnd = time.time()
            timeElapsed = timeEnd - timeBegin
            if timeElapsed > self.timeSeconds:
                timeElapsed = self.timeSeconds
            time.sleep(self.timeSeconds-timeElapsed)