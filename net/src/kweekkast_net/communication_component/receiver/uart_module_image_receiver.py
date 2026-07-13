from kweekkast_net.communication_component.receiver.uart_core_data_receiver import UartCoreDataReceiver


class UartModuleImageReceiver(UartCoreDataReceiver):
    def __init__(self, image_client, port: str = "/dev/serial0", baudrate: int = 115200, serial_connection=None, image_reassembler=None):
        super().__init__(
            telemetry_client=None,
            image_client=image_client,
            port=port,
            baudrate=baudrate,
            serial_connection=serial_connection,
            image_reassembler=image_reassembler,
        )
