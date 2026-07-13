import serial

from kweekkast_common.logger_component import console_logger, file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.net_core_protocol import (
    FrameStreamDecoder,
    FrameType,
    decode_frame,
    decode_module_telemetry_frame,
)


class UartModuleTelemetryReceiver:
    def __init__(self, telemetry_client, port: str = "/dev/serial0", baudrate: int = 115200, serial_connection=None):
        self.telemetry_client = telemetry_client
        self.running = True
        self._decoder = FrameStreamDecoder()
        self._serial = serial_connection or serial.Serial(port=port, baudrate=baudrate, timeout=1)

    def process_bytes(self, data: bytes) -> int:
        uploaded_count = 0
        for frame in self._decoder.feed(data):
            decoded_frame = decode_frame(frame)
            if decoded_frame.frame_type != FrameType.MODULE_TELEMETRY_SNAPSHOT:
                continue

            telemetry = decode_module_telemetry_frame(frame)
            self.telemetry_client.upload_telemetry(telemetry)
            uploaded_count += 1
            file_logger.logger.log(
                MessageSeverity.INFO,
                self.__class__.__name__,
                f"Telemetry dataset met {len(telemetry)} modules geupload",
            )

        return uploaded_count

    def read_once(self) -> int:
        data = self._serial.read(64)
        if not data:
            return 0
        return self.process_bytes(data)

    def start_listening(self) -> None:
        try:
            while self.running:
                try:
                    self.read_once()
                except Exception as exc:
                    message = f"Telemetry upload failed: {exc!r}"
                    file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__, message)
                    console_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__, message)
        finally:
            close = getattr(self.telemetry_client, "close", None)
            if close:
                close()

    def stop_listening(self) -> None:
        self.running = False

    def close(self) -> None:
        self._serial.close()
