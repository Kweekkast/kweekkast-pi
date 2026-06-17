from abc import ABC, abstractmethod

from kweekkast_common.communication_component.connection import Connection


class ConnectionListener(ABC):
    def __init__(self, distributer: "CommunicatorDistributor"):
        self.distributer = distributer

    @abstractmethod
    def HandleIncommingDevices(self) -> None:
        pass

    @abstractmethod
    def StopReadingIncommingDevices(self) -> None:
        pass

    @abstractmethod
    def CreateConnection(self, identifier: str) -> Connection:
        pass
