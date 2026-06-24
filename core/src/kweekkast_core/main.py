import os
import threading
import time

import serial

from kweekkast_common.communication_component.communicator_distributor import CommunicatorDistributor
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.serial_frame_transport import SerialFrameTransport
from kweekkast_core.communication_component.receiver.uart_module_command_receiver import UartModuleCommandReceiver
from kweekkast_core.communication_component.transmitter.core_telemetry_transmitter import CoreTelemetryTransmitter
from kweekkast_core.communication_component.transmitter.core_image_transmitter import CoreImageTransmitter, QueuedImageTransmitter
from kweekkast_core.image_capturing.camera_component_handler import CameraComponentHandler
from kweekkast_core.image_capturing.triggers.timer_trigger import TimerTrigger


class Main:
    def run(self) -> None:
        net_uart = self._open_net_uart()
        telemetry_transmitter = self._create_telemetry_transmitter(net_uart)
        command_receiver = self._create_command_receiver(net_uart)
        distributor = CommunicatorDistributor(telemetry_transmitter=telemetry_transmitter)
        distributor.StartAllListeners()
        if command_receiver:
            threading.Thread(
                target=command_receiver.start_listening,
                name="UartModuleCommandReceiver",
                daemon=True,
            ).start()

        image_transmitter = self._create_image_transmitter(net_uart)
        camera_component_handler = CameraComponentHandler(
            TimerTrigger(float(os.environ.get("KWEEK_CAMERA_INTERVAL_SECONDS", "30"))),
            int(os.environ.get("KWEEK_CAMERA_COUNT", "3")),
            image_transmitter=image_transmitter,
        )
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
            if telemetry_transmitter:
                telemetry_transmitter.close()
            if command_receiver:
                command_receiver.stop_listening()
                command_receiver.close()
            elif net_uart:
                net_uart.close()
            distributor.Disconnect()

    def _open_net_uart(self):
        try:
            serial_connection = serial.Serial(
                port=os.environ.get("KWEEK_CORE_UART_PORT", "/dev/serial0"),
                baudrate=int(os.environ.get("KWEEK_CORE_UART_BAUD", "115200")),
                timeout=1,
            )
            return SerialFrameTransport(serial_connection)
        except Exception as exc:
            file_logger.logger.log(
                MessageSeverity.ERROR,
                self.__class__.__name__,
                f"UART naar net Pi niet beschikbaar; config, telemetry en image upload zijn uitgeschakeld: {exc!r}",
            )
            return None

    def _create_image_transmitter(self, serial_connection=None):
        if serial_connection is None:
            return None
        try:
            return QueuedImageTransmitter(
                CoreImageTransmitter(
                    serial_connection=serial_connection,
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

    def _create_telemetry_transmitter(self, serial_connection=None):
        if serial_connection is None:
            return None
        try:
            return CoreTelemetryTransmitter(
                serial_connection=serial_connection,
            )
        except Exception as exc:
            file_logger.logger.log(
                MessageSeverity.ERROR,
                self.__class__.__name__,
                f"Telemetry UART transmitter niet beschikbaar; sensordata wordt niet naar net Pi gestuurd: {exc!r}",
            )
            return None

    def _create_command_receiver(self, serial_connection=None):
        if serial_connection is None:
            return None
        try:
            return UartModuleCommandReceiver(
                serial_connection=serial_connection,
            )
        except Exception as exc:
            file_logger.logger.log(
                MessageSeverity.ERROR,
                self.__class__.__name__,
                f"Command UART receiver niet beschikbaar; actuatoren ontvangen geen signed config: {exc!r}",
            )
            return None


def main() -> None:
    Main().run()


if __name__ == "__main__":
    main()
