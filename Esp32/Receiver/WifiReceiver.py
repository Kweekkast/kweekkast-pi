from __future__ import annotations
from typing import TYPE_CHECKING

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
        print(f"[WifiReceiver] Luisteren op {self.connection.host}:{self.connection.port}")
        # TODO: implementeer wifi luisteren