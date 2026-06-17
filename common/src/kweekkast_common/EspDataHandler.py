from __future__ import annotations

from kweekkast_common.communication_component.Subscriber import Subscriber
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
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
            file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                                   f"Doorsturen naar Pi: {reading.message}")
            piCommunicator.director.HandleReading(reading)
        else:
            file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                                   f"Geen Pi gevonden om naar door te sturen")