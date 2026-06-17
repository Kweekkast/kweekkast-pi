from kweekkast_common.transmitter.transmitter import Transmitter
from kweekkast_core.connection.serial_connection import SerialConnection


class SerialTransmitter(Transmitter):

    def __init__(self, connection: SerialConnection):
        self.serial = connection.serial

    def SendMessage(self, message: str) -> None:
        if self.serial.is_open:
            print("Send message back")
            self.serial.write(message.encode())
