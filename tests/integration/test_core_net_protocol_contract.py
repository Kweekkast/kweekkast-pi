def test_application_entry_points_are_importable() -> None:
    from kweekkast_core.main import main as core_main
    from kweekkast_net.main import main as net_main

    assert callable(core_main)
    assert callable(net_main)


def test_cross_package_factories_are_importable() -> None:
    from kweekkast_common.communication_component.communicator import Communicator
    from kweekkast_common.communication_component.director import Director
    from kweekkast_common.logger_component.file_logger import FileLogger
    from kweekkast_common.communication_component.receiver import Receiver
    from kweekkast_common.communication_component.transmitter import Transmitter
    from kweekkast_core.image_capturing.camera_component_handler import CameraComponentHandler
    from kweekkast_core.communication_component.listener.serial_connection_listener import SerialConnectionListener

    assert Communicator is not None
    assert Director is not None
    assert Receiver is not None
    assert Transmitter is not None
    assert CameraComponentHandler is not None
    assert FileLogger is not None
    assert SerialConnectionListener is not None


def test_core_main_reuses_one_uart_transport_for_net_pi_paths(monkeypatch) -> None:
    import kweekkast_core.main as core_main_module

    serial_connection = FakeSerial()
    monkeypatch.setattr(core_main_module.serial, "Serial", lambda **kwargs: serial_connection)

    main = core_main_module.Main()
    transport = main._open_net_uart()
    telemetry_transmitter = main._create_telemetry_transmitter(transport)
    image_transmitter = main._create_image_transmitter(transport)
    command_receiver = main._create_command_receiver(transport)

    assert telemetry_transmitter._serial is transport
    assert image_transmitter.transmitter._serial is transport
    assert command_receiver._serial is transport

    image_transmitter.close()
    telemetry_transmitter.close()
    command_receiver.close()
    assert serial_connection.close_count == 1


def test_serial_frame_transport_writes_and_flushes_complete_frames() -> None:
    from kweekkast_common.serial_frame_transport import SerialFrameTransport

    serial_connection = FakeSerial()
    transport = SerialFrameTransport(serial_connection)

    transport.write_frame(b"frame-1")
    transport.write_frame(b"frame-2")
    transport.close()
    transport.close()

    assert serial_connection.written == [b"frame-1", b"frame-2"]
    assert serial_connection.flush_count == 2
    assert serial_connection.close_count == 1


class FakeSerial:
    def __init__(self):
        self.written = []
        self.flush_count = 0
        self.close_count = 0

    def write(self, data: bytes) -> int:
        self.written.append(data)
        return len(data)

    def flush(self) -> None:
        self.flush_count += 1

    def read(self, size: int) -> bytes:
        return b""

    def close(self) -> None:
        self.close_count += 1
