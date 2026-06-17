def test_application_entry_points_are_importable() -> None:
    from kweekkast_core.main import main as core_main
    from kweekkast_net.main import main as net_main

    assert callable(core_main)
    assert callable(net_main)


def test_cross_package_factories_are_importable() -> None:
    from kweekkast_common.communicator import Communicator
    from kweekkast_common.director.director import Director
    from kweekkast_common.loggers.debug_logger import DebugLogger
    from kweekkast_common.loggers.error_logger import ErrorLogger
    from kweekkast_common.loggers.info_logger import InfoLogger
    from kweekkast_common.loggers.warning_logger import WarningLogger
    from kweekkast_common.receiver.receiver import Receiver
    from kweekkast_common.transmitter.transmitter import Transmitter
    from kweekkast_core.listener.serial_connection_listener import SerialConnectionListener
    from kweekkast_net.connection.wifi_connection import WifiConnection

    assert Communicator is not None
    assert Director is not None
    assert DebugLogger is not None
    assert ErrorLogger is not None
    assert InfoLogger is not None
    assert WarningLogger is not None
    assert Receiver is not None
    assert Transmitter is not None
    assert SerialConnectionListener is not None
    assert WifiConnection is not None
