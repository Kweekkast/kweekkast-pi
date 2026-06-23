import serial

from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.net_core_protocol import (
    FrameStreamDecoder,
    FrameType,
    decode_frame,
    decode_module_command_frame,
)
from kweekkast_core.communication_component.actuator_sink import GpioModuleActuatorSink, ModuleActuatorSink


class LoggingModuleCommandHandler:
    def apply(self, commands) -> None:
        file_logger.logger.log(
            MessageSeverity.DEV,
            self.__class__.__name__,
            f"Received module command snapshot: {commands}",
        )


class UartModuleCommandReceiver:
    def __init__(
        self,
        handler: ModuleActuatorSink | None = None,
        port: str = "/dev/serial0",
        baudrate: int = 115200,
        serial_connection=None,
    ):
        self.handler = handler or GpioModuleActuatorSink()
        self.running = True
        self._decoder = FrameStreamDecoder()
        self._serial = serial_connection or serial.Serial(port=port, baudrate=baudrate, timeout=1)

    def process_bytes(self, data: bytes) -> int:
        applied_count = 0
        for frame in self._decoder.feed(data):
            decoded_frame = decode_frame(frame)
            if decoded_frame.frame_type != FrameType.MODULE_COMMAND_SNAPSHOT:
                continue

            commands = decode_module_command_frame(frame)
            self.handler.apply(commands)
            applied_count += 1
            file_logger.logger.log(
                MessageSeverity.INFO,
                self.__class__.__name__,
                f"Module command snapshot met {len(commands)} modules toegepast",
            )

        return applied_count

    def read_once(self) -> int:
        data = self._serial.read(64)
        if not data:
            return 0
        return self.process_bytes(data)

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
