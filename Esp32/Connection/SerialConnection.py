from serial import Serial
from Esp32.Connection.Connection import Connection, ConnectionType


class SerialConnection(Connection):

    def __init__(self, port: str, baudrate: int = 115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial = Serial(port, baudrate)
        self.type = ConnectionType.SERIAL

    def __repr__(self) -> str:
        return f"SerialConnection(port={self.port!r}, baudrate={self.baudrate})"