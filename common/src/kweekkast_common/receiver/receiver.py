from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kweekkast_common.communicator import Communicator
    from kweekkast_common.connection.connection import Connection

from kweekkast_common.connection.connection import ConnectionType


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
        # TODO: decouple
        match connection.type:
            case ConnectionType.SERIAL:
                from kweekkast_core.receiver.serial_receiver import SerialReceiver

                return SerialReceiver(communicator, connection)
            case ConnectionType.WIFI:
                from kweekkast_net.receiver.wifi_receiver import WifiReceiver

                return WifiReceiver(communicator, connection)
            case _:
                raise ValueError(f"Unknown connection type: {connection.type}")
