from kweekkast_common.transmitter.transmitter import Transmitter
from kweekkast_net.connection.wifi_connection import WifiConnection


class WifiTransmitter(Transmitter):

    def __init__(self, connection: WifiConnection):
        pass

    def SendMessage(self, message: str) -> None:
        # TODO: implementeer wifi verzenden
        pass
