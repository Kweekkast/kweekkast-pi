from dataclasses import dataclass
from enum import IntEnum
import json
import struct
from typing import Any


MAGIC = 0x4B
MAX_PAYLOAD_LENGTH = 255


class FrameType(IntEnum):
    MODULE_COMMAND_SNAPSHOT = 0x01
    MODULE_TELEMETRY_SNAPSHOT = 0x02


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class ModuleCommand:
    module_id: int
    pump: bool
    day: bool
    grow: bool


@dataclass(frozen=True)
class ModuleTelemetry:
    module_id: int
    time: int
    water_temperature: float
    water_ph: float
    water_tds: int
    air_temperature: float
    air_humidity: float


TELEMETRY_MODULE_COUNT = 3
TELEMETRY_MODULE_STRUCT = struct.Struct(">BIhHHhH")


def parse_module_commands_json(data: Any) -> list[ModuleCommand]:
    if not isinstance(data, dict):
        raise ProtocolError("Endpoint response must be a JSON object.")

    modules = data.get("modules")
    if not isinstance(modules, list):
        raise ProtocolError("Endpoint response must contain a 'modules' list.")

    commands = []
    seen_ids = set()
    for module in modules:
        if not isinstance(module, dict):
            raise ProtocolError("Each module must be a JSON object.")

        module_id = _parse_module_id(module.get("id"))
        if module_id in seen_ids:
            raise ProtocolError(f"Duplicate module id: {module_id}")
        seen_ids.add(module_id)

        commands.append(
            ModuleCommand(
                module_id=module_id,
                pump=_parse_bool_field(module, "pump"),
                day=_parse_bool_field(module, "day"),
                grow=_parse_bool_field(module, "grow"),
            )
        )

    return commands


def parse_module_telemetry_message(message: str) -> list[ModuleTelemetry]:
    try:
        data = json.loads(message)
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"Telemetry message is not valid JSON: {exc.msg}") from exc

    return parse_module_telemetry_json(data)


def parse_module_telemetry_json(data: Any) -> list[ModuleTelemetry]:
    if not isinstance(data, dict):
        raise ProtocolError("Telemetry message must be a JSON object.")

    modules = data.get("modules")
    if not isinstance(modules, list):
        raise ProtocolError("Telemetry message must contain a 'modules' list.")
    if len(modules) != TELEMETRY_MODULE_COUNT:
        raise ProtocolError(f"Telemetry message must contain exactly {TELEMETRY_MODULE_COUNT} modules.")

    telemetry = []
    seen_ids = set()
    for module in modules:
        if not isinstance(module, dict):
            raise ProtocolError("Each telemetry module must be a JSON object.")

        module_id = _parse_module_id(module.get("module_id"))
        if module_id in seen_ids:
            raise ProtocolError(f"Duplicate module id: {module_id}")
        seen_ids.add(module_id)

        telemetry.append(
            ModuleTelemetry(
                module_id=module_id,
                time=_parse_uint(module.get("time"), "time", 0xFFFF_FFFF),
                water_temperature=_parse_number(module.get("water_temperature"), "water_temperature"),
                water_ph=_parse_number(module.get("water_ph"), "water_ph"),
                water_tds=_parse_uint(module.get("water_tds"), "water_tds", 0xFFFF),
                air_temperature=_parse_number(module.get("air_temperature"), "air_temperature"),
                air_humidity=_parse_number(module.get("air_humidity"), "air_humidity"),
            )
        )

    for module in telemetry:
        _scaled_signed_16(module.water_temperature, 100, "water_temperature")
        _scaled_unsigned_16(module.water_ph, 1000, "water_ph", maximum_value=14.0)
        _scaled_signed_16(module.air_temperature, 100, "air_temperature")
        _scaled_unsigned_16(module.air_humidity, 100, "air_humidity", maximum_value=100.0)

    return telemetry


def module_telemetry_to_endpoint_json(telemetry: list[ModuleTelemetry]) -> dict[str, list[dict[str, int | float]]]:
    return {
        "modules": [
            {
                "module_id": module.module_id,
                "time": module.time,
                "water_temperature": module.water_temperature,
                "water_ph": module.water_ph,
                "water_tds": module.water_tds,
                "air_temperature": module.air_temperature,
                "air_humidity": module.air_humidity,
            }
            for module in telemetry
        ]
    }


def encode_module_command_frame(commands: list[ModuleCommand]) -> bytes:
    payload = encode_module_command_payload(commands)
    return encode_frame(FrameType.MODULE_COMMAND_SNAPSHOT, payload)


def decode_module_command_frame(frame: bytes) -> list[ModuleCommand]:
    frame_type, payload = decode_frame(frame)
    if frame_type != FrameType.MODULE_COMMAND_SNAPSHOT:
        raise ProtocolError(f"Unsupported frame type: {frame_type}")

    return decode_module_command_payload(payload)


def encode_module_telemetry_frame(telemetry: list[ModuleTelemetry]) -> bytes:
    payload = encode_module_telemetry_payload(telemetry)
    return encode_frame(FrameType.MODULE_TELEMETRY_SNAPSHOT, payload)


def decode_module_telemetry_frame(frame: bytes) -> list[ModuleTelemetry]:
    frame_type, payload = decode_frame(frame)
    if frame_type != FrameType.MODULE_TELEMETRY_SNAPSHOT:
        raise ProtocolError(f"Unsupported frame type: {frame_type}")

    return decode_module_telemetry_payload(payload)


def encode_module_command_payload(commands: list[ModuleCommand]) -> bytes:
    if len(commands) > 255:
        raise ProtocolError("A frame can contain at most 255 module commands.")

    payload = bytearray([len(commands)])
    for command in commands:
        payload.append(_validate_module_id(command.module_id))
        payload.append(_flags_for(command))

    return bytes(payload)


def decode_module_command_payload(payload: bytes) -> list[ModuleCommand]:
    if not payload:
        raise ProtocolError("Module command payload is empty.")

    count = payload[0]
    expected_length = 1 + count * 2
    if len(payload) != expected_length:
        raise ProtocolError(f"Invalid module command payload length: expected {expected_length}, got {len(payload)}.")

    commands = []
    seen_ids = set()
    offset = 1
    for _ in range(count):
        module_id = payload[offset]
        flags = payload[offset + 1]
        offset += 2

        if flags & 0b1111_1000:
            raise ProtocolError(f"Reserved flag bits are set for module {module_id}.")
        if module_id in seen_ids:
            raise ProtocolError(f"Duplicate module id: {module_id}")
        seen_ids.add(module_id)

        commands.append(
            ModuleCommand(
                module_id=module_id,
                pump=bool(flags & 0b0000_0001),
                day=bool(flags & 0b0000_0010),
                grow=bool(flags & 0b0000_0100),
            )
        )

    return commands


def encode_module_telemetry_payload(telemetry: list[ModuleTelemetry]) -> bytes:
    _validate_telemetry_count(telemetry)

    payload = bytearray([len(telemetry)])
    for module in telemetry:
        payload.extend(
            TELEMETRY_MODULE_STRUCT.pack(
                _validate_module_id(module.module_id),
                _parse_uint(module.time, "time", 0xFFFF_FFFF),
                _scaled_signed_16(module.water_temperature, 100, "water_temperature"),
                _scaled_unsigned_16(module.water_ph, 1000, "water_ph", maximum_value=14.0),
                _parse_uint(module.water_tds, "water_tds", 0xFFFF),
                _scaled_signed_16(module.air_temperature, 100, "air_temperature"),
                _scaled_unsigned_16(module.air_humidity, 100, "air_humidity", maximum_value=100.0),
            )
        )

    return bytes(payload)


def decode_module_telemetry_payload(payload: bytes) -> list[ModuleTelemetry]:
    if not payload:
        raise ProtocolError("Telemetry payload is empty.")

    count = payload[0]
    if count != TELEMETRY_MODULE_COUNT:
        raise ProtocolError(f"Telemetry payload must contain exactly {TELEMETRY_MODULE_COUNT} modules.")

    expected_length = 1 + count * TELEMETRY_MODULE_STRUCT.size
    if len(payload) != expected_length:
        raise ProtocolError(f"Invalid telemetry payload length: expected {expected_length}, got {len(payload)}.")

    telemetry = []
    seen_ids = set()
    offset = 1
    for _ in range(count):
        (
            module_id,
            timestamp,
            water_temperature,
            water_ph,
            water_tds,
            air_temperature,
            air_humidity,
        ) = TELEMETRY_MODULE_STRUCT.unpack_from(payload, offset)
        offset += TELEMETRY_MODULE_STRUCT.size

        if module_id in seen_ids:
            raise ProtocolError(f"Duplicate module id: {module_id}")
        seen_ids.add(module_id)

        telemetry.append(
            ModuleTelemetry(
                module_id=module_id,
                time=timestamp,
                water_temperature=water_temperature / 100,
                water_ph=water_ph / 1000,
                water_tds=water_tds,
                air_temperature=air_temperature / 100,
                air_humidity=air_humidity / 100,
            )
        )

    return telemetry


def encode_frame(frame_type: FrameType, payload: bytes) -> bytes:
    if len(payload) > MAX_PAYLOAD_LENGTH:
        raise ProtocolError(f"Payload is too long: {len(payload)} bytes.")

    frame_without_crc = bytes([MAGIC, int(frame_type), len(payload)]) + payload
    return frame_without_crc + bytes([crc8(frame_without_crc)])


def decode_frame(frame: bytes) -> tuple[FrameType, bytes]:
    if len(frame) < 4:
        raise ProtocolError("Frame is too short.")
    if frame[0] != MAGIC:
        raise ProtocolError("Frame magic byte is invalid.")

    try:
        frame_type = FrameType(frame[1])
    except ValueError as exc:
        raise ProtocolError(f"Unknown frame type: {frame[1]}") from exc

    payload_length = frame[2]
    expected_length = 4 + payload_length
    if len(frame) != expected_length:
        raise ProtocolError(f"Invalid frame length: expected {expected_length}, got {len(frame)}.")

    expected_crc = crc8(frame[:-1])
    actual_crc = frame[-1]
    if actual_crc != expected_crc:
        raise ProtocolError(f"Invalid frame CRC: expected {expected_crc:#04x}, got {actual_crc:#04x}.")

    return frame_type, frame[3:-1]


class FrameStreamDecoder:
    def __init__(self):
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[bytes]:
        self._buffer.extend(data)
        frames = []

        while True:
            magic_index = self._find_magic()
            if magic_index is None:
                self._buffer.clear()
                return frames
            if magic_index > 0:
                del self._buffer[:magic_index]

            if len(self._buffer) < 3:
                return frames

            payload_length = self._buffer[2]
            frame_length = 4 + payload_length
            if len(self._buffer) < frame_length:
                return frames

            candidate = bytes(self._buffer[:frame_length])
            del self._buffer[:frame_length]

            try:
                decode_frame(candidate)
            except ProtocolError:
                continue

            frames.append(candidate)

    def _find_magic(self) -> int | None:
        try:
            return self._buffer.index(MAGIC)
        except ValueError:
            return None


def crc8(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def _parse_module_id(value: Any) -> int:
    if not isinstance(value, int):
        raise ProtocolError("Module id must be an integer.")
    return _validate_module_id(value)


def _validate_module_id(module_id: int) -> int:
    if not 0 <= module_id <= 255:
        raise ProtocolError(f"Module id must fit in one byte: {module_id}")
    return module_id


def _parse_bool_field(module: dict[str, Any], field_name: str) -> bool:
    value = module.get(field_name)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False

    raise ProtocolError(f"Module field '{field_name}' must be 'true' or 'false'.")


def _parse_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ProtocolError(f"Telemetry field '{field_name}' must be numeric.")
    return float(value)


def _parse_uint(value: Any, field_name: str, maximum_value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProtocolError(f"Telemetry field '{field_name}' must be an integer.")
    if not 0 <= value <= maximum_value:
        raise ProtocolError(f"Telemetry field '{field_name}' must be between 0 and {maximum_value}.")
    return value


def _scaled_signed_16(value: float, scale: int, field_name: str) -> int:
    scaled = round(_parse_number(value, field_name) * scale)
    if not -32768 <= scaled <= 32767:
        raise ProtocolError(f"Telemetry field '{field_name}' is outside the int16 fixed-point range.")
    return scaled


def _scaled_unsigned_16(value: float, scale: int, field_name: str, maximum_value: float) -> int:
    number = _parse_number(value, field_name)
    if not 0 <= number <= maximum_value:
        raise ProtocolError(f"Telemetry field '{field_name}' must be between 0 and {maximum_value}.")

    scaled = round(number * scale)
    if not 0 <= scaled <= 65535:
        raise ProtocolError(f"Telemetry field '{field_name}' is outside the uint16 fixed-point range.")
    return scaled


def _validate_telemetry_count(telemetry: list[ModuleTelemetry]) -> None:
    if len(telemetry) != TELEMETRY_MODULE_COUNT:
        raise ProtocolError(f"Telemetry frames must contain exactly {TELEMETRY_MODULE_COUNT} modules.")

    seen_ids = set()
    for module in telemetry:
        if module.module_id in seen_ids:
            raise ProtocolError(f"Duplicate module id: {module.module_id}")
        seen_ids.add(module.module_id)


def _flags_for(command: ModuleCommand) -> int:
    flags = 0
    if command.pump:
        flags |= 0b0000_0001
    if command.day:
        flags |= 0b0000_0010
    if command.grow:
        flags |= 0b0000_0100
    return flags
