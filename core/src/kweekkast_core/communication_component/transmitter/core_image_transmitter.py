from __future__ import annotations

import queue
import threading

import serial

from kweekkast_common.net_core_protocol import encode_module_image_chunk_frame, iter_module_image_chunks
from kweekkast_core.image_capturing.captured_image import CapturedImage


class CoreImageTransmitter:
    def __init__(
        self,
        port: str = "/dev/serial0",
        baudrate: int = 115200,
        serial_connection=None,
    ):
        self.port = port
        self.baudrate = baudrate
        self._serial = serial_connection or serial.Serial(port=port, baudrate=baudrate, timeout=1)

    def send_image(self, image: CapturedImage) -> None:
        timestamp = int(image.captured_at.timestamp())
        for chunk in iter_module_image_chunks(
            message_id=image.message_id,
            module_id=image.module_id,
            timestamp=timestamp,
            image_bytes=image.jpeg_bytes,
        ):
            self.send_frame(encode_module_image_chunk_frame(chunk))

    def send_frame(self, frame: bytes) -> None:
        write_frame = getattr(self._serial, "write_frame", None)
        if write_frame:
            write_frame(frame)
            return
        self._serial.write(frame)
        self._serial.flush()

    def close(self) -> None:
        self._serial.close()


class QueuedImageTransmitter:
    def __init__(self, transmitter: CoreImageTransmitter, queue_size: int = 3):
        self.transmitter = transmitter
        self._queue: queue.Queue[CapturedImage | None] = queue.Queue(maxsize=queue_size)
        self._running = True
        self._thread = threading.Thread(target=self._worker, name="CoreImageTransmitter", daemon=True)
        self._thread.start()

    def send_image(self, image: CapturedImage) -> None:
        if self._queue.full():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                pass
        self._queue.put_nowait(image)

    def close(self) -> None:
        self._running = False
        if self._queue.full():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                pass
        self._queue.put_nowait(None)
        self._thread.join(timeout=2)
        self.transmitter.close()

    def _worker(self) -> None:
        while self._running:
            try:
                image = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                if image is None:
                    return
                self.transmitter.send_image(image)
            finally:
                self._queue.task_done()
