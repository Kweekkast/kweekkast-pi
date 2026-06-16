from __future__ import annotations
from typing import TYPE_CHECKING

import serial

if TYPE_CHECKING:
    from Esp32.Communicator import Communicator

from Esp32.Connection.SerialConnection import SerialConnection
from Esp32.Receiver.Receiver import Receiver


class SerialReceiver(Receiver):

    def __init__(self, communicator: "Communicator", connection: SerialConnection):
        super().__init__(communicator, connection)
        self.serial = connection.serial

    def ReadLine(self) -> str:
        return self.serial.readline().decode("utf-8", errors="replace").strip()

    def StartListening(self) -> None:
        print(f"[SerialReceiver] Luisteren op {self.connection.port}")
        while self.running:
            try:
                if self.serial.is_open:
                    line = self.ReadLine()
                    if line:
                        print(f"[SerialReceiver] Ontvangen op {self.connection.port}: {line}")
                        self.communicator.UpdateReading(line)
            except serial.SerialException:
                print(f"[SerialReceiver] Verbinding verloren op {self.connection.port}")
                self._running = False