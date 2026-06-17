import serial

from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.net_core_protocol import FrameStreamDecoder, decode_module_command_frame


class ModuleCommandHandler:
    def apply(self, commands) -> None:
        raise NotImplementedError


class LoggingModuleCommandHandler(ModuleCommandHandler):
    def apply(self, commands) -> None:
        file_logger.logger.log(
            MessageSeverity.DEV,
            self.__class__.__name__,
            f"Received module command snapshot: {commands}",
        )


class UartModuleCommandReceiver:
    def __init__(
        self,
        handler: ModuleCommandHandler,
        port: str = "/dev/serial0",
        baudrate: int = 115200,
        serial_connection=None,
    ):
        self.handler = handler
        self.running = True
        self._decoder = FrameStreamDecoder()
        self._serial = serial_connection or serial.Serial(port=port, baudrate=baudrate, timeout=1)

    def start_listening(self) -> None:
        while self.running:
            data = self._serial.read(64)
            if not data:
                continue

            for frame in self._decoder.feed(data):
                commands = decode_module_command_frame(frame)
                self.handler.apply(commands)

    def stop_listening(self) -> None:
        self.running = False

    def close(self) -> None:
        self._serial.close()
