from __future__ import annotations
import threading
from typing import TYPE_CHECKING

from Esp32.Reading import Reading
from Esp32.Connection.Connection import Connection
from Esp32.Subject import Subject

if TYPE_CHECKING:
    from Esp32.Director.Director import Director
    from Esp32.Transmitter.Transmitter import Transmitter


class Communicator(Subject):

    def __init__(self, connection: Connection):
        super().__init__()
        self.connection = connection
        self.reading = Reading()
        self.director: "Director | None" = None

        from Esp32.Receiver.Receiver import Receiver
        self.receiver = Receiver.CreateReceiver(self, connection)

        self._receiverThread = threading.Thread(
            target=self.receiver.StartListening,
            name=f"Receiver-{connection}",
            daemon=True
        )
        self._receiverThread.start()

    def Init(self, transmitter: "Transmitter", directorClass: type) -> None:
        """Koppel een Director aan deze Communicator na aanmaken."""
        self.director = directorClass(self, transmitter)

    def UpdateReading(self, message: str) -> None:
        self.reading = Reading(message, self.ValidateMessage(message))
        self.NotifyAll()

    def ValidateMessage(self, message: str) -> bool:
        # TODO: voeg protocol-specifieke validatie toe
        return bool(message)