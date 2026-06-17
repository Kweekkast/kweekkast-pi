from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
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
        file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"Luisteren op {self.connection.host}:{self.connection.port}")
        # TODO: implementeer wifi luisteren
