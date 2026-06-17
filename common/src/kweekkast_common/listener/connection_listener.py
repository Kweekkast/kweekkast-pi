from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from kweekkast_common.connection.connection import Connection


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
