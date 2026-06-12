from __future__ import annotations
import threading
from contextlib import nullcontext

from Esp32.Connection.Connection import Connection
from Esp32.Communicator import Communicator


class CommunicatorDistributer:
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
        self.communicators[identifier] = communicator
        print(f"[Distributer] Communicator aangemaakt voor {identifier}")

    def RemoveConnection(self, identifier: str) -> None:
        communicator = self.communicators.pop(identifier, None)
        if communicator:
            communicator.receiver.StopListening()
            print(f"[Distributer] Communicator verwijderd voor {identifier}")