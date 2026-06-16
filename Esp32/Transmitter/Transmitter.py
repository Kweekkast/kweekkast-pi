from abc import ABC, abstractmethod
from Esp32.Connection.Connection import ConnectionType, Connection


class Transmitter(ABC):

    @abstractmethod
    def SendMessage(self, message: str) -> None:
        pass

    @staticmethod
    def CreateTransmitter(connection: "Connection") -> "Transmitter":
        # Importeer hier om circulaire imports te vermijden
        from Esp32.Transmitter.SerialTransmitter import SerialTransmitter
        from Esp32.Transmitter.WifiTransmitter import WifiTransmitter

        match connection.type:
            case ConnectionType.SERIAL:
                return SerialTransmitter(connection)
            case ConnectionType.WIFI:
                return WifiTransmitter(connection)
            case _:
                raise ValueError(f"Onbekend connection type: {connection.type}")