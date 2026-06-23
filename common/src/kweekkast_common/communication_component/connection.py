from abc import ABC
from enum import Enum


# TODO: decouple
class ConnectionType(Enum):
    SERIAL = 1


# TODO: decouple
class ConnectionDevice(Enum):
    PI = 1
    ESP = 2


class Connection(ABC):
    def __init__(self):
        self.type: ConnectionType
        self.device: ConnectionDevice
