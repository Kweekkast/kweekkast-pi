from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Esp32.Communicator import Communicator

from Esp32.Reading import Reading
from Esp32.Connection.Connection import ConnectionDevice


class Director(ABC):
    """
    Eén Director per Communicator.
    Verwerkt binnenkomende readings en stuurt via een eigen Transmitter terug.
    """

    def __init__(self, communicator: "Communicator"):
        self.communicator = communicator

        from Esp32.Transmitter.Transmitter import Transmitter
        self.transmitter = Transmitter.CreateTransmitter(communicator.connection)

    @abstractmethod
    def HandleReading(self, reading: Reading) -> None:
        pass

    def SendMessage(self, message: str) -> None:
        self.transmitter.SendMessage(message)

    @staticmethod
    def CreateDirector(communicator: "Communicator") -> "Director":
        from Esp32.Director.EspDirector import EspDirector
        from Esp32.Director.PiDirector import PiDirector

        match communicator.connection.device:
            case ConnectionDevice.ESP:
                return EspDirector(communicator)
            case ConnectionDevice.PI:
                return PiDirector(communicator)
            case _:
                raise ValueError(f"Onbekend device: {communicator.connection.device}")