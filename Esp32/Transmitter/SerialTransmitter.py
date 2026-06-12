from serial import Serial
from Esp32.Reading import Reading
from Esp32.Transmitter.Transmitter import Transmitter


class SerialTransmitter(Transmitter):

    def __init__(self, serial: Serial):
        self.serial = serial

    def SendMessage(self, reading: Reading) -> None:
        if self.serial.is_open:
            print("Send message back")
            if reading.valid:
                # TODO validate message maken
                self.serial.write("ACK".encode())

            elif not reading.valid:
                # TODO niet validate message maken
                self.serial.write("NACK".encode())