import time
from Esp32.CommunicatorDistributer import CommunicatorDistributer
from Esp32.Director.EspDirector import EspDirector
from Esp32.Transmitter.SerialTransmitter import SerialTransmitter
from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger
from LoggerComponent.LoggerEnum import MessageSeverity
from ImageCapturing.CameraComponentHandler import CameraComponentHandler
from ImageCapturing.Triggers.TimerTrigger import TimerTrigger


class Main:
    def run(self) -> None:
        cameraComponentHandler = CameraComponentHandler(TimerTrigger(30),1)
        cameraComponentHandler.run()

        distributer = CommunicatorDistributer()
        distributer.StartAllListeners()

        print("[Main] Systeem gestart. Wachten op apparaten... (Ctrl+C om te stoppen)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[Main] Gestopt.")


if __name__ == "__main__":
    Main().run()