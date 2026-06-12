from abc import ABC, abstractmethod
from Esp32.Reading import Reading


class Transmitter(ABC):

    @abstractmethod
    def SendMessage(self, reading: Reading) -> None:
        pass