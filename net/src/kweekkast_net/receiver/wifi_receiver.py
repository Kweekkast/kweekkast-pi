from typing import TYPE_CHECKING

from kweekkast_net.connection.wifi_connection import WifiConnection

if TYPE_CHECKING:
    from kweekkast_common.communicator import Communicator

from kweekkast_common.receiver.receiver import Receiver


class WifiReceiver(Receiver):

    def __init__(self, communicator: "Communicator", connection: WifiConnection):
        super().__init__(communicator, connection)
        # TODO: wifi socket opzetten

    def ReadLine(self) -> str:
        # TODO: implementeer wifi lezen
        return ""

    def StartListening(self) -> None:
        print(f"[WifiReceiver] Luisteren op {self.connection.host}:{self.connection.port}")
        # TODO: implementeer wifi luisteren
