from serial import Serial

from Esp32.Connection.SerialConnection import SerialConnection
from Esp32.Transmitter.Transmitter import Transmitter


class SerialTransmitter(Transmitter):

    def __init__(self, connection: SerialConnection):
        self.serial = connection.serial

    def SendMessage(self, message: str) -> None:
        if self.serial.is_open:
            print("Send message back")
            self.serial.write(message.encode())