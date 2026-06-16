from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Esp32.CommunicatorDistributer import CommunicatorDistributer

from Esp32.Connection.Connection import Connection


class ConnectionListener(ABC):
    def __init__(self, distributer: "CommunicatorDistributer"):
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