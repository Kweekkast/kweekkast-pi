from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.communication_component.transmitter import Transmitter
from kweekkast_core.communication_component.connection.serial_connection import SerialConnection


class SerialTransmitter(Transmitter):

    def __init__(self, connection: SerialConnection):
        self.serial = connection.serial

    def SendMessage(self, message: str) -> None:
        if self.serial.is_open:
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"Send message back: {message}")
            self.serial.write(f"{message}\n".encode())
            self.serial.flush()
