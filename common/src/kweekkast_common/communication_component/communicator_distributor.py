import threading

from kweekkast_common.communication_component.communicator import Communicator
from kweekkast_common.communication_component.connection import Connection, ConnectionDevice
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_core.communication_component.esp_data_handler import EspDataHandler
from kweekkast_common.gpio.gpio_controller import GpioController

class CommunicatorDistributor:
    def __init__(self):
        self.communicators: dict[str, Communicator] = {}
        self.listeners = []
        self.gpioController = GpioController()
        self.espDataHandler = EspDataHandler(self, self.gpioController)

    def StartAllListeners(self) -> None:
        # Imports hier binnen de methode — zo ontstaat er geen circulaire import
        from kweekkast_common.communication_component.connection_listener import ConnectionListener
        from kweekkast_core.communication_component.listener.serial_connection_listener import SerialConnectionListener

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

    def Forward(self, source: Communicator) -> None:
        """Stuur het bericht van een ESP32 door naar de Pi-communicator."""
        piCommunicator = self.FindPiCommunicator()
        if piCommunicator:
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"Doorsturen naar Pi: {source.reading.message}")
            piCommunicator.UpdateReading(source.reading.message)
        else:
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, "Geen Pi gevonden om naar door te sturen")

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
