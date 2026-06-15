from __future__ import annotations
import threading
from typing import TYPE_CHECKING

from Esp32.Reading import Reading
from Esp32.Connection.Connection import Connection
from Esp32.Subject import Subject


class Communicator(Subject):

    def __init__(self, connection: Connection):
        super().__init__()
        self.connection = connection
        self.reading = Reading()

        from Esp32.Director.Director import Director
        self.director = Director.CreateDirector(self)

        from Esp32.Receiver.Receiver import Receiver
        self.receiver = Receiver.CreateReceiver(self, connection)

        self._receiverThread = threading.Thread(
            target=self.receiver.StartListening,
            name=f"Receiver-{connection}",
            daemon=True
        )
        self._receiverThread.start()

    def UpdateReading(self, message: str) -> None:
        self.reading = Reading(message, self.ValidateMessage(message))
        self.director.HandleReading(self.reading)
        self.NotifyAll()

    def ValidateMessage(self, message: str) -> bool:
        # TODO: voeg protocol-specifieke validatie toe
        return bool(message)