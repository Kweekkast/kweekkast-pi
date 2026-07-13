from __future__ import annotations

import threading


class SerialFrameTransport:
    """Small thread-safe wrapper around a pyserial connection.

    The core Pi can write telemetry and image frames from different threads while
    simultaneously reading signed command frames. Reads and writes can happen in
    parallel, but each complete write+flush frame is serialized.
    """

    def __init__(self, serial_connection):
        self._serial = serial_connection
        self._write_lock = threading.Lock()
        self._close_lock = threading.Lock()
        self._closed = False

    def write_frame(self, frame: bytes) -> None:
        with self._write_lock:
            self._serial.write(frame)
            self._serial.flush()

    def write(self, data: bytes) -> int:
        with self._write_lock:
            return self._serial.write(data)

    def flush(self) -> None:
        with self._write_lock:
            self._serial.flush()

    def read(self, size: int) -> bytes:
        return self._serial.read(size)

    def close(self) -> None:
        with self._close_lock:
            if self._closed:
                return
            self._serial.close()
            self._closed = True
