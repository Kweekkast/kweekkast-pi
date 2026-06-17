from abc import ABC, abstractmethod


class Observer(ABC):

    @abstractmethod
    def Notify(self) -> None:
        pass
