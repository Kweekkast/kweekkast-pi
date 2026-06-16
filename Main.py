import time
from Esp32.CommunicatorDistributer import CommunicatorDistributer
from Esp32.Director.EspDirector import EspDirector
from Esp32.Transmitter.SerialTransmitter import SerialTransmitter
from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger
from LoggerComponent.LoggerEnum import MessageSeverity


class Main:
    def run(self) -> None:

        FileLogger.logger.Log(MessageSeverity.DEV, FileLogger.logger.__class__.__name__, "this is a test message that should be logged in a file")
        ConsoleLogger.logger.Log(MessageSeverity.DEV, ConsoleLogger.logger.__class__.__name__, "this is a test message that should be logged in the console")

        FileLogger.logger.Log(MessageSeverity.DEV, FileLogger.logger.__class__.__name__,"this is a test message that should be logged in a file")
        ConsoleLogger.logger.Log(MessageSeverity.DEV, ConsoleLogger.logger.__class__.__name__, "this is a test message that should be logged in the console")


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