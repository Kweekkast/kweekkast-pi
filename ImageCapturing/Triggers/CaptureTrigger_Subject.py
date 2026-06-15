import StringGenerators

class CaptureTrigger_Subject:
    
    def __init__(self):
        self._observerlist = []

    def AddObserver(self, newObserver):
        if not hasattr(newObserver, "notify"):                      #this if statement makes sure the object has a notify() method. 
            raise TypeError("Observer must implement notify()")     #which is basically the only way to ensure only (functionally) observers can populate it. Yay for ducktyping :(
        
        self._observerlist.append(newObserver)
        print(StringGenerators.fetchCustomDateString() + ": CaptureTrigger_Subject: Observer was added to list")

    def removeObserver(self, oldObserver):
        self._observerlist.remove(oldObserver)
        print(StringGenerators.fetchCustomDateString() + ": CaptureTrigger_Subject: Observer was removed from list")

    def notifyAllObservers(self):
        print(StringGenerators.fetchCustomDateString() + ": CaptureTrigger_Subject: Notifying all Observers")

        for observer in self._observerlist:
            try:
                observer.notify()
                print(StringGenerators.fetchCustomDateString() + ": CaptureTrigger_Subject: an Observer from the list was notified")
            except:
                print(StringGenerators.fetchCustomDateString() + ": CaptureTrigger_Subject: " + observer + " could not be notified")
                continue

        print(StringGenerators.fetchCustomDateString() + ": CaptureTrigger_Subject: All Observers were notified")
            