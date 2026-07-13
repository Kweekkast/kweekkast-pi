from abc import ABC, abstractmethod

from kweekkast_common.reading import Reading


class Subscriber(ABC):

    @abstractmethod
    def Notify(self, reading: Reading) -> None:
        pass
