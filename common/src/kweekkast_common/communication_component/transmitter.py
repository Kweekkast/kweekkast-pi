from abc import ABC, abstractmethod

from kweekkast_common.communication_component.connection import ConnectionType, Connection


class Transmitter(ABC):

    @abstractmethod
    def SendMessage(self, message: str) -> None:
        pass

    @staticmethod
    def CreateTransmitter(connection: "Connection") -> "Transmitter":
        # Importeer hier om circulaire imports te vermijden
        match connection.type:
            case ConnectionType.SERIAL:
                from kweekkast_core.communication_component.transmitter.serial_transmitter import SerialTransmitter

                return SerialTransmitter(connection)
            case ConnectionType.WIFI:
                from kweekkast_net.communication_component.transmitter.wifi_transmitter import WifiTransmitter

                return WifiTransmitter(connection)
            case _:
                raise ValueError(f"Unknown connection type: {connection.type}")
