from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Esp32.CommunicatorDistributer import CommunicatorDistributer

from Esp32.Broker.Subscriber import Subscriber
from Esp32.Connection.Connection import ConnectionDevice
from Esp32.Reading import Reading


class EspDataHandler(Subscriber):
    """
    Ontvangt data van ESP-communicators en stuurt deze door naar de Pi-communicator.
    """

    def __init__(self, distributer: "CommunicatorDistributer"):
        self.distributer = distributer

    def Notify(self, reading: Reading) -> None:
        piCommunicator = self.distributer.FindPiCommunicator()
        if piCommunicator and piCommunicator.director:
            print(f"[EspDataHandler] Doorsturen naar Pi: {reading.message}")
            piCommunicator.director.HandleReading(reading)
        else:
            print(f"[EspDataHandler] Geen Pi gevonden om naar door te sturen")