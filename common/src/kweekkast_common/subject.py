from kweekkast_common.observer import Observer

class Subject:
    def __init__(self):
        self.activeObservers = []

    def Subscribe(self, newObserver: Observer) -> None:
        self.activeObservers.append(newObserver)

    def UnSubscribe(self, oldObserver: Observer) -> None:
        if oldObserver in self.activeObservers:
            self.activeObservers.remove(oldObserver)

    def NotifyAll(self) -> None:
        for observer in self.activeObservers:
            observer.Notify()
