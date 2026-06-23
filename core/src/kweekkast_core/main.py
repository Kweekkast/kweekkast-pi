import os
import time

from kweekkast_common.communication_component.communicator_distributor import CommunicatorDistributor
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_core.communication_component.transmitter.core_image_transmitter import CoreImageTransmitter, QueuedImageTransmitter
from kweekkast_core.image_capturing.camera_component_handler import CameraComponentHandler
from kweekkast_core.image_capturing.triggers.timer_trigger import TimerTrigger


class Main:
    def run(self) -> None:
        distributor = CommunicatorDistributor()
        distributor.StartAllListeners()

        image_transmitter = self._create_image_transmitter()
        camera_component_handler = CameraComponentHandler(TimerTrigger(30), 3, image_transmitter=image_transmitter)
        camera_component_handler.run()

        file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                               f"Systeem gestart. Wachten op apparaten... (Ctrl+C om te stoppen)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                                   f"Gestopt")
            if image_transmitter:
                image_transmitter.close()
            distributor.Disconnect()

    def _create_image_transmitter(self):
        try:
            return QueuedImageTransmitter(
                CoreImageTransmitter(
                    port=os.environ.get("KWEEK_CORE_UART_PORT", "/dev/serial0"),
                    baudrate=int(os.environ.get("KWEEK_CORE_UART_BAUD", "115200")),
                ),
                queue_size=int(os.environ.get("KWEEK_IMAGE_QUEUE_SIZE", "3")),
            )
        except Exception as exc:
            file_logger.logger.log(
                MessageSeverity.ERROR,
                self.__class__.__name__,
                f"Image UART transmitter niet beschikbaar; beelden worden alleen lokaal opgeslagen: {exc!r}",
            )
            return None


def main() -> None:
    Main().run()


if __name__ == "__main__":
    main()
