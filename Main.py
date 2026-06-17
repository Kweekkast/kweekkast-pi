import time
from Esp32.CommunicatorDistributer import CommunicatorDistributer
from ImageCapturing.camera_component_handler import CameraComponentHandler
from ImageCapturing.Triggers.timer_trigger import TimerTrigger


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
            distributer.Disconnect()
            print("[Main] Gestopt.")


if __name__ == "__main__":
    Main().run()