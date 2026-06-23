import os
import threading

from kweekkast_net.communication_component.receiver.uart_module_telemetry_receiver import UartModuleTelemetryReceiver
from kweekkast_net.communication_component.transmitter.uart_module_command_transmitter import UartModuleCommandTransmitter
from kweekkast_net.module_command_client import ModuleCommandClient
from kweekkast_net.module_command_sync import ModuleCommandSyncService
from kweekkast_net.module_telemetry_client import ModuleTelemetryClient


def main() -> None:
    command_endpoint_url = os.environ.get("KWEEK_ENDPOINT_URL")
    telemetry_endpoint_url = os.environ.get("KWEEK_TELEMETRY_ENDPOINT_URL")
    api_token = os.environ.get("KWEEK_API_TOKEN") or os.environ.get("KWEEKKAST_API_TOKEN")
    allow_insecure_http = os.environ.get("KWEEK_ALLOW_INSECURE_HTTP", "false").lower() == "true"
    if not command_endpoint_url and not telemetry_endpoint_url:
        raise SystemExit("KWEEK_ENDPOINT_URL or KWEEK_TELEMETRY_ENDPOINT_URL is required.")

    command_uart_port = os.environ.get("KWEEK_NET_UART_PORT", "/dev/serial0")
    command_baudrate = int(os.environ.get("KWEEK_NET_UART_BAUD", "115200"))
    poll_seconds = float(os.environ.get("KWEEK_POLL_SECONDS", "10"))

    telemetry_receiver = None
    if telemetry_endpoint_url:
        telemetry_uart_port = os.environ.get("KWEEK_CORE_UART_PORT", "/dev/serial0")
        telemetry_baudrate = int(os.environ.get("KWEEK_CORE_UART_BAUD", "115200"))
        telemetry_client = ModuleTelemetryClient(
            telemetry_endpoint_url,
            api_token=api_token,
            allow_insecure_http=allow_insecure_http,
        )
        telemetry_receiver = UartModuleTelemetryReceiver(telemetry_client, telemetry_uart_port, telemetry_baudrate)

    if command_endpoint_url:
        if telemetry_receiver:
            threading.Thread(
                target=telemetry_receiver.start_listening,
                name="CoreTelemetryReceiver",
                daemon=True,
            ).start()

        client = ModuleCommandClient(
            command_endpoint_url,
            api_token=api_token,
            allow_insecure_http=allow_insecure_http,
        )
        transmitter = UartModuleCommandTransmitter(command_uart_port, command_baudrate)
        service = ModuleCommandSyncService(client, transmitter, poll_seconds)
        service.run_forever()
    elif telemetry_receiver:
        telemetry_receiver.start_listening()


if __name__ == "__main__":
    main()
