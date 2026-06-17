from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger
from LoggerComponent.LoggerEnum import MessageSeverity
from typing import TYPE_CHECKING

from kweekkast_common.receiver.receiver import Receiver
from kweekkast_net.connection.wifi_connection import WifiConnection


class WifiReceiver(Receiver):

    def __init__(self, communicator: "Communicator", connection: WifiConnection):
        super().__init__(communicator, connection)
        # TODO: wifi socket opzetten

    def ReadLine(self) -> str:
        # TODO: implementeer wifi lezen
        return ""

    def StartListening(self) -> None:
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,
                              f" Luisteren op {self.connection.host}:{self.connection.port}")
        # TODO: implementeer wifi luisteren
