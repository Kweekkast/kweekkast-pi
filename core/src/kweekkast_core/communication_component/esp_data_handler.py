from __future__ import annotations

import json
import time

from kweekkast_common.communication_component.subscriber import Subscriber
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.net_core_protocol import ModuleTelemetry, ProtocolError, parse_module_telemetry_message
from kweekkast_common.reading import Reading


LEGACY_ESP_FIELD_MAP = {
    "ModuleActive": "module_id",
    "WaterTemperatuur": "water_temperature",
    "PH_Water": "water_ph",
    "TDS_Water": "water_tds",
    "KamerTemperatuur": "air_temperature",
    "LuchtVochtigheidKamer": "air_humidity",
}
EXPECTED_TELEMETRY_MODULE_IDS = (1, 2, 3)


class EspDataHandler(Subscriber):
    """
    Handles fakeable ESP input.

    - With telemetry_transmitter: parse sensor snapshots and forward them to the net Pi.
    - With gpio_controller: retain the Development-style control/sensor JSON path.
    """

    def __init__(
        self,
        distributer,
        gpio_controller=None,
        telemetry_transmitter=None,
        *,
        expected_module_ids=EXPECTED_TELEMETRY_MODULE_IDS,
        clock=time.time,
    ):
        self.distributer = distributer
        self.gpio_controller = gpio_controller
        self.telemetry_transmitter = telemetry_transmitter
        self.expected_module_ids = tuple(expected_module_ids)
        self._clock = clock
        self._latest_telemetry_by_module: dict[int, ModuleTelemetry] = {}

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
            self._handle_legacy_esp_telemetry(reading.message, exc)
            return

        self._send_telemetry_snapshot(telemetry)

    def _handle_legacy_esp_telemetry(self, message: str, original_error: ProtocolError) -> None:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"Niet-JSON ESP regel genegeerd: {message}")
            return

        try:
            telemetry = legacy_esp_json_to_module_telemetry(data, timestamp=int(self._clock()))
        except ProtocolError:
            file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__, f"Ongeldige ESP telemetry: {original_error}")
            return

        if telemetry.module_id not in self.expected_module_ids:
            file_logger.logger.log(
                MessageSeverity.WARNING,
                self.__class__.__name__,
                f"ESP telemetry voor onverwachte module {telemetry.module_id} genegeerd",
            )
            return

        self._latest_telemetry_by_module[telemetry.module_id] = telemetry
        missing_module_ids = [
            module_id
            for module_id in self.expected_module_ids
            if module_id not in self._latest_telemetry_by_module
        ]
        if missing_module_ids:
            file_logger.logger.log(
                MessageSeverity.INFO,
                self.__class__.__name__,
                f"ESP telemetry module {telemetry.module_id} geaccepteerd; wacht op modules {missing_module_ids}",
            )
            return

        snapshot = [
            self._latest_telemetry_by_module[module_id]
            for module_id in self.expected_module_ids
        ]
        self._latest_telemetry_by_module.clear()
        self._send_telemetry_snapshot(snapshot)

    def _send_telemetry_snapshot(self, telemetry: list[ModuleTelemetry]) -> None:
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


def legacy_esp_json_to_module_telemetry(data: dict, *, timestamp: int) -> ModuleTelemetry:
    if not isinstance(data, dict):
        raise ProtocolError("Legacy ESP telemetry must be a JSON object.")

    missing_fields = [
        field_name
        for field_name in LEGACY_ESP_FIELD_MAP
        if field_name not in data
    ]
    if missing_fields:
        raise ProtocolError(f"Legacy ESP telemetry is missing fields: {missing_fields}")

    try:
        module_id = int(data["ModuleActive"])
        water_tds = round(float(data["TDS_Water"]))
        return ModuleTelemetry(
            module_id=module_id,
            time=timestamp,
            water_temperature=float(data["WaterTemperatuur"]),
            water_ph=float(data["PH_Water"]),
            water_tds=water_tds,
            air_temperature=float(data["KamerTemperatuur"]),
            air_humidity=float(data["LuchtVochtigheidKamer"]),
        )
    except (TypeError, ValueError) as exc:
        raise ProtocolError("Legacy ESP telemetry contains invalid numeric values.") from exc
