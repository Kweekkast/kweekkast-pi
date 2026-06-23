from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from enum import IntEnum
import hashlib
import json
import math
import struct
from typing import Any
import uuid
import zlib

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


PROTOCOL_VERSION = 1
MAX_PAYLOAD_LENGTH = 4096
FRAME_DELIMITER = 0x00
SIGNED_CONFIG_SCHEMA_VERSION = 2
SIGNED_CONFIG_PAYLOAD_SCHEMA_VERSION = 1
SIGNATURE_ALGORITHM = "Ed25519"

_HEADER = struct.Struct(">BBIH")
_CRC32 = struct.Struct(">I")
_MAX_UINT32 = 0xFFFF_FFFF


class FrameType(IntEnum):
    MODULE_COMMAND_SNAPSHOT = 0x01
    MODULE_TELEMETRY_SNAPSHOT = 0x02
    SIGNED_MODULE_COMMAND_CONFIG = 0x03


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


@dataclass(frozen=True)
class DecodedFrame:
    frame_type: FrameType
    sequence: int
    payload: bytes


@dataclass(frozen=True)
class VerifiedSignedCommandConfig:
    envelope: dict[str, Any]
    payload: dict[str, Any]
    commands: list[ModuleCommand]
    config_sequence: int
    valid_for_seconds: int
    key_id: str


TELEMETRY_MODULE_COUNT = 3
TELEMETRY_MODULE_STRUCT = struct.Struct(">BIhHHhH")


def parse_module_commands_json(data: Any) -> list[ModuleCommand]:
    if not isinstance(data, dict):
        raise ProtocolError("Endpoint response must be a JSON object.")
    if data.get("schema_version") != 1:
        raise ProtocolError("Endpoint response must use schema_version 1.")

    modules = data.get("modules")
    if not isinstance(modules, list):
        raise ProtocolError("Endpoint response must contain a 'modules' list.")

    commands = []
    seen_ids = set()
    for module in modules:
        if not isinstance(module, dict):
            raise ProtocolError("Each module must be a JSON object.")

        module_id = _parse_module_id(module.get("module_id"))
        if module_id in seen_ids:
            raise ProtocolError(f"Duplicate module id: {module_id}")
        seen_ids.add(module_id)

        outputs = module.get("outputs")
        if not isinstance(outputs, dict):
            raise ProtocolError("Each module must contain an 'outputs' object.")
        unknown_outputs = set(outputs) - {"pump", "day", "grow"}
        if unknown_outputs:
            raise ProtocolError(f"Unknown output fields: {sorted(unknown_outputs)}")

        commands.append(
            ModuleCommand(
                module_id=module_id,
                pump=_parse_bool_field(outputs, "pump"),
                day=_parse_bool_field(outputs, "day"),
                grow=_parse_bool_field(outputs, "grow"),
            )
        )

    return commands


def validate_signed_command_config_envelope(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ProtocolError("Signed config envelope must be a JSON object.")
    if data.get("schema_version") != SIGNED_CONFIG_SCHEMA_VERSION:
        raise ProtocolError(f"Signed config envelope must use schema_version {SIGNED_CONFIG_SCHEMA_VERSION}.")

    payload = data.get("payload")
    if not isinstance(payload, dict):
        raise ProtocolError("Signed config envelope must contain a payload object.")
    _validate_signed_config_payload(payload)

    signature = data.get("signature")
    if not isinstance(signature, dict):
        raise ProtocolError("Signed config envelope must contain a signature object.")
    if signature.get("alg") != SIGNATURE_ALGORITHM:
        raise ProtocolError(f"Signed config signature must use {SIGNATURE_ALGORITHM}.")
    if not isinstance(signature.get("key_id"), str) or not signature["key_id"]:
        raise ProtocolError("Signed config signature must contain a key_id.")
    if not isinstance(signature.get("value"), str) or not signature["value"]:
        raise ProtocolError("Signed config signature must contain a value.")

    return data


def verify_signed_command_config(
    envelope: Any,
    public_keys: dict[str, str],
) -> VerifiedSignedCommandConfig:
    envelope = validate_signed_command_config_envelope(envelope)
    payload = envelope["payload"]
    signature = envelope["signature"]
    key_id = signature["key_id"]

    if key_id not in public_keys:
        raise ProtocolError(f"Unknown config signing key id: {key_id}")

    try:
        public_key_bytes = base64url_decode(public_keys[key_id])
        signature_bytes = base64url_decode(signature["value"])
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature_bytes, canonical_json_bytes(payload))
    except (ValueError, binascii.Error, InvalidSignature) as exc:
        raise ProtocolError("Config signature verification failed.") from exc

    commands = parse_module_commands_json(payload)
    return VerifiedSignedCommandConfig(
        envelope=envelope,
        payload=payload,
        commands=commands,
        config_sequence=payload["config_sequence"],
        valid_for_seconds=payload["valid_for_seconds"],
        key_id=key_id,
    )


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


def module_telemetry_to_endpoint_json(
    telemetry: list[ModuleTelemetry],
    *,
    message_id: uuid.UUID | str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "message_id": str(message_id or uuid.uuid4()),
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
        ],
    }


def encode_module_command_frame(commands: list[ModuleCommand], *, sequence: int = 0) -> bytes:
    payload = encode_module_command_payload(commands)
    return encode_frame(FrameType.MODULE_COMMAND_SNAPSHOT, payload, sequence=sequence)


def decode_module_command_frame(frame: bytes) -> list[ModuleCommand]:
    decoded_frame = decode_frame(frame)
    if decoded_frame.frame_type != FrameType.MODULE_COMMAND_SNAPSHOT:
        raise ProtocolError(f"Unsupported frame type: {decoded_frame.frame_type}")

    return decode_module_command_payload(decoded_frame.payload)


def encode_signed_module_command_config_frame(envelope: dict[str, Any], *, sequence: int = 0) -> bytes:
    validate_signed_command_config_envelope(envelope)
    return encode_frame(
        FrameType.SIGNED_MODULE_COMMAND_CONFIG,
        canonical_json_bytes(envelope),
        sequence=sequence,
    )


def decode_signed_module_command_config_frame(frame: bytes) -> dict[str, Any]:
    decoded_frame = decode_frame(frame)
    if decoded_frame.frame_type != FrameType.SIGNED_MODULE_COMMAND_CONFIG:
        raise ProtocolError(f"Unsupported frame type: {decoded_frame.frame_type}")

    try:
        envelope = json.loads(decoded_frame.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("Signed module command config frame does not contain valid JSON.") from exc

    return validate_signed_command_config_envelope(envelope)


def encode_module_telemetry_frame(telemetry: list[ModuleTelemetry], *, sequence: int = 0) -> bytes:
    payload = encode_module_telemetry_payload(telemetry)
    return encode_frame(FrameType.MODULE_TELEMETRY_SNAPSHOT, payload, sequence=sequence)


def decode_module_telemetry_frame(frame: bytes) -> list[ModuleTelemetry]:
    decoded_frame = decode_frame(frame)
    if decoded_frame.frame_type != FrameType.MODULE_TELEMETRY_SNAPSHOT:
        raise ProtocolError(f"Unsupported frame type: {decoded_frame.frame_type}")

    return decode_module_telemetry_payload(decoded_frame.payload)


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


def encode_frame(frame_type: FrameType | int, payload: bytes, *, sequence: int = 0) -> bytes:
    resolved_type = _frame_type(frame_type)
    if not 0 <= sequence <= _MAX_UINT32:
        raise ProtocolError("sequence must fit in an unsigned 32-bit integer.")
    if len(payload) > MAX_PAYLOAD_LENGTH:
        raise ProtocolError(f"Payload is too long: {len(payload)} bytes.")

    body = _HEADER.pack(PROTOCOL_VERSION, resolved_type.value, sequence, len(payload)) + payload
    checksum = _CRC32.pack(zlib.crc32(body) & _MAX_UINT32)
    return cobs_encode(body + checksum) + bytes((FRAME_DELIMITER,))


def decode_frame(encoded_frame: bytes, *, max_payload_length: int = MAX_PAYLOAD_LENGTH) -> DecodedFrame:
    if encoded_frame.endswith(bytes((FRAME_DELIMITER,))):
        encoded_frame = encoded_frame[:-1]

    raw = cobs_decode(encoded_frame)
    raw_max_length = _HEADER.size + max_payload_length + _CRC32.size
    if len(raw) < _HEADER.size + _CRC32.size:
        raise ProtocolError("Frame is shorter than header and CRC.")
    if len(raw) > raw_max_length:
        raise ProtocolError(f"Decoded frame is too long: {len(raw)} bytes.")

    body = raw[:-_CRC32.size]
    expected_crc = zlib.crc32(body) & _MAX_UINT32
    actual_crc = _CRC32.unpack(raw[-_CRC32.size:])[0]
    if actual_crc != expected_crc:
        raise ProtocolError("CRC mismatch.")

    version, frame_type, sequence, payload_length = _HEADER.unpack(body[: _HEADER.size])
    if version != PROTOCOL_VERSION:
        raise ProtocolError(f"Unsupported protocol version: {version}")
    if payload_length > max_payload_length:
        raise ProtocolError(f"Payload is too long: {payload_length} bytes.")

    payload = body[_HEADER.size:]
    if len(payload) != payload_length:
        raise ProtocolError("Payload length does not match frame header.")

    return DecodedFrame(_frame_type(frame_type), sequence, payload)


class FrameStreamDecoder:
    def __init__(self, *, max_payload_length: int = MAX_PAYLOAD_LENGTH):
        raw_max_length = _HEADER.size + max_payload_length + _CRC32.size
        self.max_payload_length = max_payload_length
        self.max_encoded_length = max_cobs_encoded_size(raw_max_length)
        self._buffer = bytearray()
        self._dropping_oversized_frame = False

    def feed(self, data: bytes) -> list[bytes]:
        frames = []

        for value in data:
            if value == FRAME_DELIMITER:
                if self._dropping_oversized_frame:
                    self._dropping_oversized_frame = False
                    self._buffer.clear()
                    continue
                if not self._buffer:
                    continue

                candidate = bytes(self._buffer)
                self._buffer.clear()
                try:
                    decode_frame(candidate, max_payload_length=self.max_payload_length)
                except ProtocolError:
                    continue
                frames.append(candidate)
                continue

            if self._dropping_oversized_frame:
                continue

            self._buffer.append(value)
            if len(self._buffer) > self.max_encoded_length:
                self._buffer.clear()
                self._dropping_oversized_frame = True

        return frames


def cobs_encode(data: bytes) -> bytes:
    if not data:
        return b"\x01"

    encoded = bytearray()
    block_start = 0

    for index, value in enumerate(data):
        if value == FRAME_DELIMITER:
            encoded.append(index - block_start + 1)
            encoded.extend(data[block_start:index])
            block_start = index + 1
        elif index - block_start == 253:
            encoded.append(0xFF)
            encoded.extend(data[block_start : index + 1])
            block_start = index + 1

    if block_start < len(data) or data[-1] == FRAME_DELIMITER:
        encoded.append(len(data) - block_start + 1)
        encoded.extend(data[block_start:])

    return bytes(encoded)


def cobs_decode(data: bytes) -> bytes:
    if not data:
        raise ProtocolError("Empty COBS frame.")

    decoded = bytearray()
    index = 0

    while index < len(data):
        code = data[index]
        if code == FRAME_DELIMITER:
            raise ProtocolError("COBS frame contains a zero byte.")

        index += 1
        block_end = index + code - 1
        if block_end > len(data):
            raise ProtocolError("COBS block overruns frame.")

        decoded.extend(data[index:block_end])
        index = block_end

        if code != 0xFF and index < len(data):
            decoded.append(FRAME_DELIMITER)

    return bytes(decoded)


def max_cobs_encoded_size(raw_size: int) -> int:
    if raw_size < 0:
        raise ValueError("raw_size must be non-negative")
    if raw_size == 0:
        return 1
    return raw_size + (raw_size // 254) + 1


def canonical_command_hash(commands: list[ModuleCommand]) -> str:
    state = [
        {
            "module_id": command.module_id,
            "outputs": {
                "pump": command.pump,
                "day": command.day,
                "grow": command.grow,
            },
        }
        for command in commands
    ]
    return hashlib.sha256(json.dumps(state, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _validate_signed_config_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != SIGNED_CONFIG_PAYLOAD_SCHEMA_VERSION:
        raise ProtocolError(f"Signed config payload must use schema_version {SIGNED_CONFIG_PAYLOAD_SCHEMA_VERSION}.")
    if not isinstance(payload.get("config_sequence"), int) or payload["config_sequence"] < 0:
        raise ProtocolError("Signed config payload must contain a non-negative integer config_sequence.")
    if not isinstance(payload.get("issued_at"), str) or not payload["issued_at"]:
        raise ProtocolError("Signed config payload must contain issued_at.")
    if not isinstance(payload.get("valid_for_seconds"), int) or payload["valid_for_seconds"] <= 0:
        raise ProtocolError("Signed config payload must contain a positive integer valid_for_seconds.")
    if not isinstance(payload.get("state_hash"), str) or len(payload["state_hash"]) != 64:
        raise ProtocolError("Signed config payload must contain a 64-character state_hash.")

    parse_module_commands_json(payload)


def _parse_module_id(value: Any) -> int:
    if not isinstance(value, int):
        raise ProtocolError("Module id must be an integer.")
    return _validate_module_id(value)


def _validate_module_id(module_id: int) -> int:
    if not 0 <= module_id <= 255:
        raise ProtocolError(f"Module id must fit in one byte: {module_id}")
    return module_id


def _parse_bool_field(module: dict[str, Any], field_name: str) -> bool:
    if field_name not in module:
        raise ProtocolError(f"Module field '{field_name}' is required.")
    value = module[field_name]
    if not isinstance(value, bool):
        raise ProtocolError(f"Module field '{field_name}' must be boolean.")
    return value


def _parse_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ProtocolError(f"Telemetry field '{field_name}' must be finite numeric.")
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


def _frame_type(value: FrameType | int) -> FrameType:
    try:
        return FrameType(value)
    except ValueError as exc:
        raise ProtocolError(f"Unknown frame type: {int(value)}") from exc
