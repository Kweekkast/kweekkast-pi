from ImageCapturing.Triggers.AbstractTrigger import Abstract_Trigger
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
            recalculatedSleeptime = self.timeSeconds-timeElapsed

            if recalculatedSleeptime < 0:
                recalculatedSleeptime = 0

            FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__, "notifying all observers took: " + str(timeElapsed) + " Seconds")
            FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__, "Sleeping " + str(recalculatedSleeptime) + " Seconds before renotifying observers")
            
            time.sleep(recalculatedSleeptime)