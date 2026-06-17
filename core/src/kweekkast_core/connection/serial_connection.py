from serial import Serial
from kweekkast_common.connection.connection import Connection, ConnectionType, ConnectionDevice


class SerialConnection(Connection):

    def __init__(self, port: str, device: ConnectionDevice, baudrate: int = 115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial = Serial(port, baudrate)
        self.type = ConnectionType.SERIAL
        self.device = device

    def __repr__(self) -> str:
        return f"SerialConnection(port={self.port!r}, device={self.device.name}, baudrate={self.baudrate})"
