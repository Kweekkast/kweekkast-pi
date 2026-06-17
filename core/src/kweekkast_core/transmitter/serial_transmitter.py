from serial import Serial

from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.transmitter.transmitter import Transmitter
from kweekkast_core.connection.serial_connection import SerialConnection


class SerialTransmitter(Transmitter):

    def __init__(self, connection: SerialConnection):
        self.serial = connection.serial

    def SendMessage(self, message: str) -> None:
        if self.serial.is_open:
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"Send message back: {message}")
            self.serial.write(message.encode())
