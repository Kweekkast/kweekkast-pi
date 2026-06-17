from abc import ABC, abstractmethod
from Esp32.Reading import Reading


class Subscriber(ABC):

    @abstractmethod
    def Notify(self, reading: Reading) -> None:
        pass