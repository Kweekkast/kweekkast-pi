import time

from kweekkast_common.communicator_distributor import CommunicatorDistributor
from Esp32.CommunicatorDistributer import CommunicatorDistributer
from ImageCapturing.camera_component_handler import CameraComponentHandler
from ImageCapturing.Triggers.timer_trigger import TimerTrigger


class Main:
    def run(self) -> None:
        distributor = CommunicatorDistributor()
        distributor.StartAllListeners()

        cameraComponentHandler = CameraComponentHandler(TimerTrigger(30),1)
        cameraComponentHandler.run()

        print("[Main] Systeem gestart. Wachten op apparaten... (Ctrl+C om te stoppen)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[Main] Gestopt.")


def main() -> None:
    Main().run()


if __name__ == "__main__":
    main()
