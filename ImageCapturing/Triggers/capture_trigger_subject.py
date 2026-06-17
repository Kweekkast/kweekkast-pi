from LoggerComponent.LoggerEnum import MessageSeverity
from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger

class CaptureTriggerSubject:
    
    def __init__(self):
        self._OBSERVERLIST = []

    def add_observer(self, newObserver):
        if hasattr(newObserver, "notify"):
            raise TypeError("Observer must implement notify()")
        
        self._OBSERVERLIST.append(newObserver)
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"Observer was added to list")

    def remove_observer(self, oldObserver):
        self._OBSERVERLIST.remove(oldObserver)
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"Observer was removed from list")

    def notify_all_observers(self):
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"Notifying all Observers")

        for observer in self._OBSERVERLIST:
            try:
                observer.notify()
                FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"an Observer from the list was notified")
            except Exception as e:
                FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__, "Something went wrong notifying:" + str(observer) + ". \n Exception:" + repr(e))
                continue

        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"All Observers were notified")
        ConsoleLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"All Observers were notified")
            