from __future__ import annotations
import threading
from Esp32.Connection.Connection import Connection, ConnectionDevice
from Esp32.Communicator import Communicator
from Esp32.Gpio.GpioController import GpioController
from Esp32.EspDataHandler import EspDataHandler

class CommunicatorDistributer:
    def __init__(self):
        self.communicators: dict[str, Communicator] = {}
        self.listeners = []
        self.gpioController = GpioController()
        self.espDataHandler = EspDataHandler(self)

    def StartAllListeners(self) -> None:
        from Esp32.Listener.ConnectionListener import ConnectionListener
        from Esp32.Listener import SerialConnectionListener

        for listenerClass in ConnectionListener.__subclasses__():
            listener = listenerClass(self)
            t = threading.Thread(
                target=listener.HandleIncommingDevices,
                name=listenerClass.__name__,
                daemon=True
            )
            self.listeners.append(listener)
            t.start()
            print(f"[Distributer] {listenerClass.__name__} gestart")

    def AddConnection(self, identifier: str, connection: Connection) -> None:
        communicator = Communicator(connection)

        if connection.device == ConnectionDevice.ESP:
            communicator.Subscribe(ConnectionDevice.ESP, self.espDataHandler)
        elif connection.device == ConnectionDevice.PI:
            communicator.Subscribe(ConnectionDevice.PI, self.gpioController)

        self.communicators[identifier] = communicator
        print(f"[Distributer] Communicator aangemaakt voor {identifier} ({connection.device.name})")

    def RemoveConnection(self, identifier: str) -> None:
        communicator = self.communicators.pop(identifier, None)
        if communicator:
            communicator.receiver.StopListening()
            print(f"[Distributer] Communicator verwijderd voor {identifier}")

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