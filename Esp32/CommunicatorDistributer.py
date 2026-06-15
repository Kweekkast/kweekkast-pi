from __future__ import annotations
import threading
from contextlib import nullcontext

from Esp32.Connection.Connection import Connection, ConnectionType, ConnectionDevice
from Esp32.Communicator import Communicator
from Esp32.Observer import Observer


class CommunicatorDistributer(Observer):
    def __init__(self):
        self.communicators: dict[str, Communicator] = {}
        self._listeners = []

    def StartAllListeners(self) -> None:
        # Imports hier binnen de methode — zo ontstaat er geen circulaire import
        from Esp32.Listener.ConnectionListener import ConnectionListener
        from Esp32.Listener import SerialConnectionListener  # registreert subklasse

        for listenerClass in ConnectionListener.__subclasses__():
            listener = listenerClass(self)
            t = threading.Thread(
                target=listener.HandleIncommingDevices,
                name=listenerClass.__name__,
                daemon=True
            )
            self._listeners.append(listener)
            t.start()
            print(f"[Distributer] {listenerClass.__name__} gestart")

    def AddConnection(self, identifier: str, connection: Connection) -> None:
        communicator = Communicator(connection)
        if communicator.connection.device == ConnectionDevice.ESP:
            communicator.Subscribe(self)

        self.communicators[identifier] = communicator
        print(f"[Distributer] Communicator aangemaakt voor {identifier}")

    def RemoveConnection(self, identifier: str) -> None:
        communicator = self.communicators.pop(identifier, None)
        if communicator and communicator.connection.device == ConnectionDevice.ESP:
            communicator.UnSubscribe(self)

        communicator.receiver.StopListening()
        print(f"[Distributer] Communicator verwijderd voor {identifier}")

    def Notify(self) -> None:
        """Wordt aangeroepen als een Communicator een nieuwe Reading heeft."""
        for communicator in self.communicators.values():
            if communicator.connection.device == ConnectionDevice.ESP:
                if communicator.reading.valid:
                    self.Forward(communicator)

    def Forward(self, source: Communicator) -> None:
        """Stuur het bericht van een ESP32 door naar de Pi-communicator."""
        piCommunicator = self.FindPiCommunicator()
        if piCommunicator:
            print(f"[Distributer] Doorsturen naar Pi: {source.reading.message}")
            piCommunicator.UpdateReading(source.reading)
        else:
            print(f"[Distributer] Geen Pi gevonden om naar door te sturen")

    def FindPiCommunicator(self) -> Communicator | None:
        """Zoek de communicator die verbonden is met de Pi (WiFi)."""
        for communicator in self.communicators.values():
            if communicator.connection.device == ConnectionDevice.PI:
                return communicator
        return None