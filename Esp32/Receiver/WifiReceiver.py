from __future__ import annotations
from typing import TYPE_CHECKING

from LoggerComponent.LoggerEnum import MessageSeverity
from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger

if TYPE_CHECKING:
    from Esp32.Communicator import Communicator

from Esp32.Connection.WifiConnection import WifiConnection
from Esp32.Receiver.Receiver import Receiver


class WifiReceiver(Receiver):

    def __init__(self, communicator: "Communicator", connection: WifiConnection):
        super().__init__(communicator, connection)
        # TODO: wifi socket opzetten

    def ReadLine(self) -> str:
        # TODO: implementeer wifi lezen
        return ""

    def StartListening(self) -> None:
        FileLogger.logger.Log(MessageSeverity.DEV,__class__.__name__,f" Luisteren op {self.connection.host}:{self.connection.port}")
        # TODO: implementeer wifi luisteren