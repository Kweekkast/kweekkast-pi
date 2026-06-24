import serial


class UartModuleCommandTransmitter:
    def __init__(self, port: str = "/dev/serial0", baudrate: int = 115200, serial_connection=None):
        self.port = port
        self.baudrate = baudrate
        self._serial = serial_connection or serial.Serial(port=port, baudrate=baudrate, timeout=1)

    def send_frame(self, frame: bytes) -> None:
        write_frame = getattr(self._serial, "write_frame", None)
        if write_frame:
            write_frame(frame)
            return
        self._serial.write(frame)
        self._serial.flush()

    def close(self) -> None:
        self._serial.close()
