from __future__ import annotations

import json

from kweekkast_common.communication_component.subscriber import Subscriber
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.net_core_protocol import ProtocolError, parse_module_telemetry_message
from kweekkast_common.reading import Reading


class EspDataHandler(Subscriber):
    """
    Handles fakeable ESP input.

    - With telemetry_transmitter: parse sensor snapshots and forward them to the net Pi.
    - With gpio_controller: retain the Development-style control/sensor JSON path.
    """

    def __init__(self, distributer, gpio_controller=None, telemetry_transmitter=None):
        self.distributer = distributer
        self.gpio_controller = gpio_controller
        self.telemetry_transmitter = telemetry_transmitter

    def Notify(self, reading: Reading) -> None:
        if not reading.valid:
            file_logger.logger.log(MessageSeverity.WARNING, self.__class__.__name__, f"Ongeldig bericht: {reading.message}")
            return

        if self.telemetry_transmitter is not None:
            self._send_telemetry(reading)
            return

        try:
            data = json.loads(reading.message)
        except json.JSONDecodeError as exc:
            file_logger.logger.log(
                MessageSeverity.ERROR,
                self.__class__.__name__,
                f"Kon bericht niet verwerken: {reading.message} ({exc})",
            )
            return

        message_type = data.get("type")
        if message_type == "control" and self.gpio_controller is not None:
            self.gpio_controller.Notify(reading)
            return
        if message_type == "sensor":
            self._forward_sensor(reading)
            return

        file_logger.logger.log(MessageSeverity.WARNING, self.__class__.__name__, f"Onbekend type: {message_type}")

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

    def _forward_sensor(self, reading: Reading) -> None:
        pi_communicator = self.distributer.FindPiCommunicator() if self.distributer is not None else None
        if pi_communicator and pi_communicator.director:
            file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__, f"Sensordata doorsturen naar Pi: {reading.message}")
            pi_communicator.director.HandleReading(reading)
        else:
            file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__, "Geen Pi gevonden om sensordata naar door te sturen")
