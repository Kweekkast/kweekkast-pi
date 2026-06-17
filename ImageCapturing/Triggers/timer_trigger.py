from ImageCapturing.Triggers.abstract_trigger import Abstract_Trigger
from LoggerComponent import FileLogger
from LoggerComponent.LoggerEnum import MessageSeverity
import time

class TimerTrigger(Abstract_Trigger):

    def __init__(self, sleep_time_seconds):
        super().__init__()
        self.SLEEP_TIME_SECONDS = sleep_time_seconds

    def triggerLoop(self):
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"The triggerloop has started")
        while True:
            time_seconds = time.time()

            super().notifyAllObservers()

            time_end = time.time()
            seconds_elapsed = time_end - time_seconds
            recalculated_sleep_time_seconds = self.SLEEP_TIME_SECONDS-seconds_elapsed

            if recalculated_sleep_time_seconds < 0:
                recalculated_sleep_time_seconds = 0

            FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__, "notifying all observers took: " + str(seconds_elapsed) + " Seconds")
            FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__, "Sleeping " + str(recalculated_sleep_time_seconds) + " Seconds before renotifying observers")
            
            time.sleep(recalculated_sleep_time_seconds)