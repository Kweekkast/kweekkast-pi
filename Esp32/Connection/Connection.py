from abc import ABC, abstractmethod
from enum import Enum


class ConnectionType(Enum):
    SERIAL = 1
    WIFI = 2

class ConnectionDevice(Enum):
    PI = 1
    ESP = 2


class Connection(ABC):
    def __init__(self):
        self.type: ConnectionType
        self.device: ConnectionDevice