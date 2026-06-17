import threading

from kweekkast_common.communicator import Communicator
from kweekkast_common.connection.connection import Connection, ConnectionDevice
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.observer import Observer

from kweekkast_common.Gpio.GpioController import GpioController

from kweekkast_common.EspDataHandler import EspDataHandler


class CommunicatorDistributor:
    def __init__(self):
        self.communicators: dict[str, Communicator] = {}
        self.listeners = []
        self.gpioController = GpioController()
        self.espDataHandler = EspDataHandler(self)

    def StartAllListeners(self) -> None:
        # Imports hier binnen de methode — zo ontstaat er geen circulaire import
        from kweekkast_common.listener.connection_listener import ConnectionListener
        from kweekkast_core.listener.serial_connection_listener import SerialConnectionListener

        for listenerClass in ConnectionListener.__subclasses__():
            listener = listenerClass(self)
            t = threading.Thread(
                target=listener.HandleIncommingDevices,
                name=listenerClass.__name__,
                daemon=True
            )
            self.listeners.append(listener)
            t.start()
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"{listenerClass.__name__} gestart")

    def AddConnection(self, identifier: str, connection: Connection) -> None:
        communicator = Communicator(connection)

        if connection.device == ConnectionDevice.ESP:
            communicator.Subscribe(ConnectionDevice.ESP, self.espDataHandler)
        elif connection.device == ConnectionDevice.PI:
            communicator.Subscribe(ConnectionDevice.PI, self.gpioController)

        self.communicators[identifier] = communicator
        file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"Communicator aangemaakt voor {identifier}")

    def RemoveConnection(self, identifier: str) -> None:
        communicator = self.communicators.pop(identifier, None)
        if communicator:
            communicator.receiver.StopListening()
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"Communicator verwijderd voor {identifier}")

    def FindPiCommunicator(self) -> Communicator | None:
        for communicator in self.communicators.values():
            if communicator.connection.device == ConnectionDevice.PI:
                return communicator
        return None

    def Disconnect(self) -> None:
        if self.gpioController:
            self.gpioController.Cleanup()
        for identifier in list(self.communicators.keys()):
            self.RemoveConnection(identifier)