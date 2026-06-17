from serial import Serial

from LoggerComponent.LoggerEnum import MessageSeverity
from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger

from kweekkast_common.transmitter.transmitter import Transmitter
from kweekkast_core.connection.serial_connection import SerialConnection


class SerialTransmitter(Transmitter):

    def __init__(self, connection: SerialConnection):
        self.serial = connection.serial

    def SendMessage(self, message: str) -> None:
        if self.serial.is_open:
            FileLogger.logger.Log(MessageSeverity.DEV,__class__.__name__,f"Send message back: {message}")
            self.serial.write(message.encode())