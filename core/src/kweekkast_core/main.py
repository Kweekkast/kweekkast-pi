import time

from kweekkast_common.communication_component.communicator_distributor import CommunicatorDistributor
from kweekkast_core.image_capturing.camera_component_handler import CameraComponentHandler
from kweekkast_core.image_capturing.triggers.timer_trigger import TimerTrigger


class Main:
    def run(self) -> None:
        distributor = CommunicatorDistributor()
        distributor.StartAllListeners()

        cameraComponentHandler = CameraComponentHandler(TimerTrigger(30), 1)
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
