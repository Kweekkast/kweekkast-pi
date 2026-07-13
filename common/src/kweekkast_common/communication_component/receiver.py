from abc import ABC, abstractmethod

from kweekkast_common.communication_component.connection import ConnectionType


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
                from kweekkast_core.communication_component.receiver.serial_receiver import SerialReceiver

                return SerialReceiver(communicator, connection)
            case _:
                raise ValueError(f"Unknown connection type: {connection.type}")
