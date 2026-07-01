import json
import os
from pathlib import Path
import time

import serial

from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.net_core_protocol import (
    FrameStreamDecoder,
    FrameType,
    ModuleCommand,
    ProtocolError,
    canonical_command_hash,
    decode_frame,
    decode_signed_module_command_config_frame,
    verify_signed_command_config,
)
from kweekkast_core.communication_component.actuator_sink import GpioModuleActuatorSink, ModuleActuatorSink


_UNSET = object()


class LoggingModuleCommandHandler:
    def apply(self, commands) -> None:
        file_logger.logger.log(
            MessageSeverity.DEV,
            self.__class__.__name__,
            f"Received module command snapshot: {commands}",
        )


class InMemorySequenceStore:
    def __init__(self, initial_sequence: int = 0):
        self.sequence = initial_sequence

    def load(self) -> int:
        return self.sequence

    def save(self, sequence: int) -> None:
        self.sequence = sequence


class FileSequenceStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> int:
        if not self.path.exists():
            return 0

        try:
            return int(self.path.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            return 0

    def save(self, sequence: int) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary_path.write_text(str(sequence), encoding="utf-8")
        temporary_path.replace(self.path)


class UartModuleCommandReceiver:
    def __init__(
        self,
        handler: ModuleActuatorSink | None = None,
        port: str = "/dev/serial0",
        baudrate: int = 115200,
        serial_connection=None,
        public_keys: dict[str, str] | None = None,
        sequence_store=None,
        safe_module_ids=(1, 2, 3),
        monotonic_clock=time.monotonic,
    ):
        self.handler = handler or GpioModuleActuatorSink()
        self.public_keys = public_keys if public_keys is not None else load_public_keys_from_env()
        self.sequence_store = sequence_store or default_sequence_store()
        self.last_accepted_sequence = self.sequence_store.load()
        self.safe_module_ids = tuple(safe_module_ids)
        self._monotonic_clock = monotonic_clock
        self._valid_until_monotonic: float | None = None
        self._safe_state_applied_for_deadline = _UNSET
        self._last_applied_command_hash: str | None = None
        self.running = True
        self._decoder = FrameStreamDecoder()
        self._serial = serial_connection or serial.Serial(port=port, baudrate=baudrate, timeout=1)

    def process_bytes(self, data: bytes) -> int:
        applied_count = 0
        for frame in self._decoder.feed(data):
            decoded_frame = decode_frame(frame)
            if decoded_frame.frame_type == FrameType.MODULE_COMMAND_SNAPSHOT:
                file_logger.logger.log(
                    MessageSeverity.WARNING,
                    self.__class__.__name__,
                    "Unsigned module command snapshot rejected.",
                )
                continue
            if decoded_frame.frame_type != FrameType.SIGNED_MODULE_COMMAND_CONFIG:
                continue

            try:
                envelope = decode_signed_module_command_config_frame(frame)
                verified_config = verify_signed_command_config(envelope, self.public_keys)
            except ProtocolError as exc:
                file_logger.logger.log(
                    MessageSeverity.WARNING,
                    self.__class__.__name__,
                    f"Signed module command config rejected: {exc}",
                )
                continue

            if verified_config.config_sequence <= self.last_accepted_sequence:
                file_logger.logger.log(
                    MessageSeverity.WARNING,
                    self.__class__.__name__,
                    f"Replayed module command config rejected: sequence {verified_config.config_sequence}.",
                )
                continue

            commands = verified_config.commands
            command_state_changed = self._apply_commands_if_changed(commands)
            self.last_accepted_sequence = verified_config.config_sequence
            self.sequence_store.save(verified_config.config_sequence)
            self._valid_until_monotonic = self._monotonic_clock() + verified_config.valid_for_seconds
            self._safe_state_applied_for_deadline = _UNSET
            applied_count += 1
            if command_state_changed:
                file_logger.logger.log(
                    MessageSeverity.INFO,
                    self.__class__.__name__,
                    f"Signed module command config sequence {verified_config.config_sequence} met {len(commands)} modules toegepast",
                )
            else:
                file_logger.logger.log(
                    MessageSeverity.DEV,
                    self.__class__.__name__,
                    f"Signed module command config sequence {verified_config.config_sequence} geaccepteerd; outputs ongewijzigd",
                )

        return applied_count

    def read_once(self) -> int:
        data = self._serial.read(64)
        if not data:
            self.apply_safe_state_if_stale()
            return 0

        processed = self.process_bytes(data)
        self.apply_safe_state_if_stale()
        return processed

    def apply_safe_state_if_stale(self) -> bool:
        deadline = self._valid_until_monotonic
        if deadline is not None and self._monotonic_clock() <= deadline:
            return False
        if self._safe_state_applied_for_deadline == deadline:
            return False

        safe_commands = [
            ModuleCommand(module_id=module_id, pump=False, day=False, grow=False)
            for module_id in self.safe_module_ids
        ]
        command_state_changed = self._apply_commands_if_changed(safe_commands)
        self._safe_state_applied_for_deadline = deadline
        if command_state_changed:
            file_logger.logger.log(
                MessageSeverity.WARNING,
                self.__class__.__name__,
                "No fresh signed module command config is active; safe state applied.",
            )
        else:
            file_logger.logger.log(
                MessageSeverity.WARNING,
                self.__class__.__name__,
                "No fresh signed module command config is active; safe state was already active.",
            )
        return True

    def _apply_commands_if_changed(self, commands: list[ModuleCommand]) -> bool:
        command_hash = canonical_command_hash(commands)
        if self._last_applied_command_hash == command_hash:
            return False

        self.handler.apply(commands)
        self._last_applied_command_hash = command_hash
        return True

    def start_listening(self) -> None:
        while self.running:
            self.read_once()

    def stop_listening(self) -> None:
        self.running = False

    def close(self) -> None:
        self._serial.close()
        close = getattr(self.handler, "close", None)
        if close:
            close()


def load_public_keys_from_env(env_name: str = "KWEEK_CONFIG_SIGNING_PUBLIC_KEYS_JSON") -> dict[str, str]:
    raw_value = os.environ.get(env_name)
    if not raw_value:
        return {}

    data = json.loads(raw_value)
    if not isinstance(data, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in data.items()):
        raise ValueError(f"{env_name} must contain a JSON object mapping key id strings to base64url public keys.")

    return data


def default_sequence_store():
    path = os.environ.get("KWEEK_CONFIG_SEQUENCE_PATH")
    if path:
        return FileSequenceStore(path)

    return InMemorySequenceStore()
