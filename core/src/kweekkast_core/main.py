import time

from kweekkast_common.communication_component.communicator_distributor import CommunicatorDistributor
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_core.image_capturing.camera_component_handler import CameraComponentHandler
from kweekkast_core.image_capturing.triggers.timer_trigger import TimerTrigger


class Main:
    def run(self) -> None:
        distributor = CommunicatorDistributor()
        distributor.StartAllListeners()

        camera_component_handler = CameraComponentHandler(TimerTrigger(30), 1)
        camera_component_handler.run()

        file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                               f"Systeem gestart. Wachten op apparaten... (Ctrl+C om te stoppen)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                                   f"Gestopt")
            distributor.Disconnect()


def main() -> None:
    Main().run()


if __name__ == "__main__":
    main()
