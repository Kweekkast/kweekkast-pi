from Esp32.Connection.Connection import Connection, ConnectionType


class WifiConnection(Connection):

    def __init__(self, host: str, port: int):
        super().__init__()
        self.host = host
        self.port = port
        self.type = ConnectionType.WIFI

    def __repr__(self) -> str:
        return f"WifiConnection(host={self.host!r}, port={self.port})"