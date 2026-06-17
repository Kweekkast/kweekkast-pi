from abc import ABC, abstractmethod


class ICaptureTriggerObserver(ABC):
    @abstractmethod
    def notify(self) -> None:
        pass
