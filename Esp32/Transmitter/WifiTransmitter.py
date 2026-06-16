from Esp32.Connection.WifiConnection import WifiConnection
from Esp32.Reading import Reading
from Esp32.Transmitter.Transmitter import Transmitter


class WifiTransmitter(Transmitter):

    def __init__(self, connection: WifiConnection):
        pass

    def SendMessage(self, message: str) -> None:
        # TODO: implementeer wifi verzenden
        pass