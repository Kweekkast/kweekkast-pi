from abc import ABC, abstractmethod


class ILogger(ABC):

    @abstractmethod
    def LogMessage(self, message: str) -> int:
        pass