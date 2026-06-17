import serial

from kweekkast_common.communicator import Communicator
from kweekkast_common.receiver.receiver import Receiver
from kweekkast_core.connection.serial_connection import SerialConnection


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
                self.running = False
