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
    from kweekkast_net.communication_component.connection.wifi_connection import WifiConnection

    assert Communicator is not None
    assert Director is not None
    assert Receiver is not None
    assert Transmitter is not None
    assert CameraComponentHandler is not None
    assert FileLogger is not None
    assert SerialConnectionListener is not None
    assert WifiConnection is not None
