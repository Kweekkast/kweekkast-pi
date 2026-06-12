from serial import Serial
from Esp32.Transmitter.Transmitter import Transmitter


class SerialTransmitter(Transmitter):

    def __init__(self, serial: Serial):
        self.serial = serial

    def SendMessage(self, message: str) -> None:
        if self.serial.is_open:
            print("Send message back")
            self.serial.write(message.encode())