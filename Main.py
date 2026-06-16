import time
from Esp32.CommunicatorDistributer import CommunicatorDistributer
from Esp32.Director.EspDirector import EspDirector
from Esp32.Transmitter.SerialTransmitter import SerialTransmitter


class Main:
    def run(self) -> None:
        distributer = CommunicatorDistributer()
        distributer.StartAllListeners()

        print("[Main] Systeem gestart. Wachten op apparaten... (Ctrl+C om te stoppen)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            distributer.Disconnect()
            print("[Main] Gestopt.")


if __name__ == "__main__":
    Main().run()