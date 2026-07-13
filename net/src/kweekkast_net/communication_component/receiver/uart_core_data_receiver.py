import serial

from kweekkast_common.logger_component import console_logger, file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.net_core_protocol import (
    FrameStreamDecoder,
    FrameType,
    ModuleImageReassembler,
    decode_frame,
    decode_module_image_chunk_frame,
    decode_module_telemetry_frame,
)


class UartCoreDataReceiver:
    def __init__(
        self,
        telemetry_client=None,
        image_client=None,
        port: str = "/dev/serial0",
        baudrate: int = 115200,
        serial_connection=None,
        image_reassembler: ModuleImageReassembler | None = None,
    ):
        self.telemetry_client = telemetry_client
        self.image_client = image_client
        self.running = True
        self._decoder = FrameStreamDecoder()
        self._image_reassembler = image_reassembler or ModuleImageReassembler()
        self._serial = serial_connection or serial.Serial(port=port, baudrate=baudrate, timeout=1)

    def process_bytes(self, data: bytes) -> int:
        uploaded_count = 0
        for frame in self._decoder.feed(data):
            decoded_frame = decode_frame(frame)
            if decoded_frame.frame_type == FrameType.MODULE_TELEMETRY_SNAPSHOT:
                if self.telemetry_client is None:
                    continue
                telemetry = decode_module_telemetry_frame(frame)
                self.telemetry_client.upload_telemetry(telemetry)
                uploaded_count += 1
                file_logger.logger.log(
                    MessageSeverity.INFO,
                    self.__class__.__name__,
                    f"Telemetry dataset met {len(telemetry)} modules geupload",
                )
                continue

            if decoded_frame.frame_type == FrameType.MODULE_IMAGE_CHUNK:
                if self.image_client is None:
                    continue
                chunk = decode_module_image_chunk_frame(frame)
                image = self._image_reassembler.feed(chunk)
                if image is None:
                    continue
                self.image_client.upload_image(image)
                uploaded_count += 1
                file_logger.logger.log(
                    MessageSeverity.INFO,
                    self.__class__.__name__,
                    f"Image voor module {image.module_id} geupload",
                )

        return uploaded_count

    def read_once(self) -> int:
        data = self._serial.read(64)
        if not data:
            self._image_reassembler.expire_stale()
            return 0
        return self.process_bytes(data)

    def start_listening(self) -> None:
        try:
            while self.running:
                try:
                    self.read_once()
                except Exception as exc:
                    message = f"Core data upload failed: {exc!r}"
                    file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__, message)
                    console_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__, message)
        finally:
            for client in (self.telemetry_client, self.image_client):
                close = getattr(client, "close", None)
                if close:
                    close()

    def stop_listening(self) -> None:
        self.running = False

    def close(self) -> None:
        self._serial.close()
