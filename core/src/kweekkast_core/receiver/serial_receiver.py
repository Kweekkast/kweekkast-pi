import serial
from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger
from LoggerComponent.LoggerEnum import MessageSeverity

from kweekkast_common.communicator import Communicator
from kweekkast_common.receiver.receiver import Receiver
from kweekkast_core.connection.serial_connection import SerialConnection


class SerialReceiver(Receiver):

    def __init__(self, communicator: "Communicator", connection: SerialConnection):
        super().__init__(communicator, connection)
        self.serial = connection.serial

    def ReadLine(self) -> str:
        return self.serial.readline().decode("utf-8", errors="replace").strip()

    def StartListening(self) -> None:
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__, f"Luisteren op {self.connection.port}")
        while True:
            try:
                if self.serial.is_open:
                    line = self.ReadLine()
                    if line:
                        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,
                                              f"Ontvangen op {self.connection.port}: {line}")
                        self.communicator.UpdateReading(line)
            except serial.SerialException:
                FileLogger.logger.Log(MessageSeverity.ERROR, __class__.__name__,
                                      f"Verbinding verloren op {self.connection.port}")
                ConsoleLogger.logger.Log(MessageSeverity.ERROR, __class__.__name__,
                                         f"Verbinding verloren op {self.connection.port}")
                break
