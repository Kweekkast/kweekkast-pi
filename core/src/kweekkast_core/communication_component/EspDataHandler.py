from __future__ import annotations

from kweekkast_common.communication_component.Subscriber import Subscriber
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.net_core_protocol import ProtocolError, parse_module_telemetry_message
from kweekkast_common.reading import Reading


class EspDataHandler(Subscriber):
    """
    Ontvangt data van ESP-communicators en stuurt deze door naar de Pi-communicator.
    """

    def __init__(self, distributer: "CommunicatorDistributer", telemetry_transmitter=None):
        self.distributer = distributer
        self.telemetry_transmitter = telemetry_transmitter

    def Notify(self, reading: Reading) -> None:
        if self.telemetry_transmitter is not None:
            self._send_telemetry(reading)
            return

        piCommunicator = self.distributer.FindPiCommunicator()
        if piCommunicator and piCommunicator.director:
            file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                                   f"Doorsturen naar Pi: {reading.message}")
            piCommunicator.director.HandleReading(reading)
        else:
            file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                                   f"Geen Pi gevonden om naar door te sturen")

    def _send_telemetry(self, reading: Reading) -> None:
        try:
            telemetry = parse_module_telemetry_message(reading.message)
        except ProtocolError as exc:
            file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__, f"Ongeldige ESP telemetry: {exc}")
            return

        self.telemetry_transmitter.send_telemetry(telemetry)
        file_logger.logger.log(
            MessageSeverity.INFO,
            self.__class__.__name__,
            f"Telemetry dataset met {len(telemetry)} modules doorgestuurd naar net Pi",
        )
