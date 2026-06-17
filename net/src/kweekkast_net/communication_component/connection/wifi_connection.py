from kweekkast_common.communication_component.connection import Connection, ConnectionType, ConnectionDevice


class WifiConnection(Connection):

    def __init__(self, host: str, port: int, device: ConnectionDevice):
        super().__init__()
        self.host = host
        self.port = port
        self.type = ConnectionType.WIFI
        self.device = device

    def __repr__(self) -> str:
        return f"WifiConnection(host={self.host!r}, port={self.port}, device={self.device.name})"
