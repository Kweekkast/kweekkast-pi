from abc import ABC, abstractmethod

from kweekkast_common.communication_component.connection import ConnectionDevice
from kweekkast_common.reading import Reading


class Director(ABC):
    """
    Eén Director per Communicator.
    Verwerkt binnenkomende readings en stuurt via een eigen Transmitter terug.
    """

    def __init__(self, communicator: "Communicator"):
        self.communicator = communicator

        from kweekkast_common.communication_component.transmitter import Transmitter
        self.transmitter = Transmitter.CreateTransmitter(communicator.connection)

    @abstractmethod
    def HandleReading(self, reading: Reading) -> None:
        pass

    def SendMessage(self, message: str) -> None:
        self.transmitter.SendMessage(message)

    # TODO: decouple
    @staticmethod
    def CreateDirector(communicator: "Communicator") -> "Director":
        match communicator.connection.device:
            case ConnectionDevice.ESP:
                from kweekkast_core.communication_component.director.esp_director import EspDirector

                return EspDirector(communicator)
            case ConnectionDevice.PI:
                from kweekkast_core.communication_component.director.pi_director import PiDirector

                return PiDirector(communicator)
            case _:
                raise ValueError(f"Onbekend device: {communicator.connection.device}")
