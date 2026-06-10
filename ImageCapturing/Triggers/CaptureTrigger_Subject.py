class CaptureTrigger_Subject:
    
    def __init__(self):
        self._observerlist = []

    def AddObserver(self, newObserver):
        if not hasattr(newObserver, "notify"):                      #this if statement makes sure the object has a notify() method. 
            raise TypeError("Observer must implement notify()")     #which is basically the only way to ensure only (functionally) observers can populate it. Yay for ducktyping :(
        
        self._observerlist.append(newObserver)

    def removeObserver(self, oldObserver):
        self._observerlist.remove(oldObserver)

    def notifyAllObservers(self):
        for observer in self._observerlist:                         #this, if it wasn't obvious, calls the notify method of all objects in the list. Let's hope no non-observers are in it!
            observer.notify()