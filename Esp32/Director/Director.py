from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Esp32.Communicator import Communicator

from Esp32.Observer import Observer
from Esp32.Reading import Reading
from Esp32.Transmitter.Transmitter import Transmitter


class Director(Observer, ABC):
    """
    Ontvangt data van een Communicator (via Observer/Subject pattern)
    en kan commando's terugsturen via een Transmitter.
    """

    def __init__(self, communicator: "Communicator", transmitter: Transmitter):
        self.communicator = communicator
        self.transmitter = transmitter
        communicator.Subscribe(self)  # registreer als observer

    def Notify(self) -> None:
        """Wordt aangeroepen door Communicator.NotifyAll() bij nieuwe Reading."""
        # self.HandleReading(self.communicator.reading)
        self.SendMessage(self.communicator.reading)

    # @abstractmethod
    # def HandleReading(self, reading: Reading) -> None:
    #     """Verwerk de binnenkomende data."""
    #     pass

    def SendMessage(self, reading: Reading) -> None:
        """Stuur een commando terug naar het apparaat."""
        self.transmitter.SendMessage(reading)