from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Esp32.Communicator import Communicator
    from Esp32.Connection.Connection import Connection

from Esp32.Connection.Connection import ConnectionType


class Receiver(ABC):
    def __init__(self, communicator: "Communicator", connection: "Connection"):
        self.communicator = communicator
        self.connection = connection
        self.running = True

    @abstractmethod
    def ReadLine(self) -> str:
        pass

    @abstractmethod
    def StartListening(self) -> None:
        pass

    def StopListening(self) -> None:
        self.running = False

    @staticmethod
    def CreateReceiver(communicator: "Communicator", connection: "Connection") -> "Receiver":
        # Importeer hier om circulaire imports te vermijden
        from Esp32.Receiver.SerialReceiver import SerialReceiver
        from Esp32.Receiver.WifiReceiver import WifiReceiver

        match connection.type:
            case ConnectionType.SERIAL:
                return SerialReceiver(communicator, connection)
            case ConnectionType.WIFI:
                return WifiReceiver(communicator, connection)
            case _:
                raise ValueError(f"Onbekend connection type: {connection.type}")