import os

from kweekkast_net.module_command_client import ModuleCommandClient
from kweekkast_net.module_command_sync import ModuleCommandSyncService
from kweekkast_net.transmitter.uart_module_command_transmitter import UartModuleCommandTransmitter


def main() -> None:
    endpoint_url = os.environ.get("KWEEK_ENDPOINT_URL")
    if not endpoint_url:
        raise SystemExit("KWEEK_ENDPOINT_URL is required.")

    uart_port = os.environ.get("KWEEK_NET_UART_PORT", "/dev/serial0")
    baudrate = int(os.environ.get("KWEEK_NET_UART_BAUD", "115200"))
    poll_seconds = float(os.environ.get("KWEEK_POLL_SECONDS", "10"))

    client = ModuleCommandClient(endpoint_url)
    transmitter = UartModuleCommandTransmitter(uart_port, baudrate)
    service = ModuleCommandSyncService(client, transmitter, poll_seconds)
    service.run_forever()


if __name__ == "__main__":
    main()
