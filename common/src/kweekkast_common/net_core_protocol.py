from dataclasses import dataclass
from enum import IntEnum
from typing import Any


MAGIC = 0x4B
MAX_PAYLOAD_LENGTH = 255


class FrameType(IntEnum):
    MODULE_COMMAND_SNAPSHOT = 0x01


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class ModuleCommand:
    module_id: int
    pump: bool
    day: bool
    grow: bool


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


def encode_module_command_frame(commands: list[ModuleCommand]) -> bytes:
    payload = encode_module_command_payload(commands)
    return encode_frame(FrameType.MODULE_COMMAND_SNAPSHOT, payload)


def decode_module_command_frame(frame: bytes) -> list[ModuleCommand]:
    frame_type, payload = decode_frame(frame)
    if frame_type != FrameType.MODULE_COMMAND_SNAPSHOT:
        raise ProtocolError(f"Unsupported frame type: {frame_type}")

    return decode_module_command_payload(payload)


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


def _flags_for(command: ModuleCommand) -> int:
    flags = 0
    if command.pump:
        flags |= 0b0000_0001
    if command.day:
        flags |= 0b0000_0010
    if command.grow:
        flags |= 0b0000_0100
    return flags
