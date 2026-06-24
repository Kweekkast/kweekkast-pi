import os
import threading

import serial

from kweekkast_common.serial_frame_transport import SerialFrameTransport
from kweekkast_net.communication_component.receiver.uart_core_data_receiver import UartCoreDataReceiver
from kweekkast_net.communication_component.transmitter.uart_module_command_transmitter import UartModuleCommandTransmitter
from kweekkast_net.module_command_client import ModuleCommandClient
from kweekkast_net.module_command_sync import ModuleCommandSyncService
from kweekkast_net.module_image_client import ModuleImageClient
from kweekkast_net.module_telemetry_client import ModuleTelemetryClient


def main() -> None:
    command_endpoint_url = os.environ.get("KWEEK_ENDPOINT_URL")
    telemetry_endpoint_url = os.environ.get("KWEEK_TELEMETRY_ENDPOINT_URL")
    image_endpoint_url = os.environ.get("KWEEK_IMAGE_ENDPOINT_URL")
    api_token = os.environ.get("KWEEK_API_TOKEN") or os.environ.get("KWEEKKAST_API_TOKEN")
    allow_insecure_http = os.environ.get("KWEEK_ALLOW_INSECURE_HTTP", "false").lower() == "true"
    if not command_endpoint_url and not telemetry_endpoint_url and not image_endpoint_url:
        raise SystemExit("KWEEK_ENDPOINT_URL, KWEEK_TELEMETRY_ENDPOINT_URL, or KWEEK_IMAGE_ENDPOINT_URL is required.")

    command_uart_port = os.environ.get("KWEEK_NET_UART_PORT", "/dev/serial0")
    command_baudrate = int(os.environ.get("KWEEK_NET_UART_BAUD", "115200"))
    poll_seconds = float(os.environ.get("KWEEK_POLL_SECONDS", "10"))
    core_uart = None
    if command_endpoint_url or telemetry_endpoint_url or image_endpoint_url:
        core_uart = SerialFrameTransport(serial.Serial(port=command_uart_port, baudrate=command_baudrate, timeout=1))

    core_data_receiver = None
    if telemetry_endpoint_url or image_endpoint_url:
        telemetry_client = ModuleTelemetryClient(
            telemetry_endpoint_url,
            api_token=api_token,
            allow_insecure_http=allow_insecure_http,
        ) if telemetry_endpoint_url else None
        image_client = ModuleImageClient(
            image_endpoint_url,
            api_token=api_token,
            allow_insecure_http=allow_insecure_http,
        ) if image_endpoint_url else None
        core_data_receiver = UartCoreDataReceiver(telemetry_client, image_client, serial_connection=core_uart)

    if command_endpoint_url:
        if core_data_receiver:
            threading.Thread(
                target=core_data_receiver.start_listening,
                name="CoreDataReceiver",
                daemon=True,
            ).start()

        client = ModuleCommandClient(
            command_endpoint_url,
            api_token=api_token,
            allow_insecure_http=allow_insecure_http,
        )
        transmitter = UartModuleCommandTransmitter(serial_connection=core_uart)
        service = ModuleCommandSyncService(client, transmitter, poll_seconds)
        service.run_forever()
    elif core_data_receiver:
        core_data_receiver.start_listening()


if __name__ == "__main__":
    main()
