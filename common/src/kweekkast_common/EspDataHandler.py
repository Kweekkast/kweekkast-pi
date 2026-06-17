from __future__ import annotations

from kweekkast_common.Broker.Subscriber import Subscriber
from kweekkast_common.reading import Reading


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