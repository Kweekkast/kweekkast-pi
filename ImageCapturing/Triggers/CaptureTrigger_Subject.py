from LoggerComponent.LoggerEnum import MessageSeverity
from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger

class CaptureTrigger_Subject:
    
    def __init__(self):
        self._observerlist = []

    def AddObserver(self, newObserver):
        if not hasattr(newObserver, "notify"):
            raise TypeError("Observer must implement notify()")
        
        self._observerlist.append(newObserver)
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"Observer was added to list")

    def removeObserver(self, oldObserver):
        self._observerlist.remove(oldObserver)
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"Observer was removed from list")

    def notifyAllObservers(self):
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"Notifying all Observers")

        for observer in self._observerlist:
            try:
                observer.notify()
                FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"an Observer from the list was notified")
            except:
                FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,observer + " could not be notified")
                continue

        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"All Observers were notified")
        ConsoleLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"All Observers were notified")
            