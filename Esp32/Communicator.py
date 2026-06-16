from __future__ import annotations
import threading

from Esp32.Broker.MessageBroker import MessageBroker
from Esp32.Reading import Reading
from Esp32.Connection.Connection import Connection


class Communicator(MessageBroker):

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
        self.Publish(self.connection.device, self.reading)

    def ValidateMessage(self, message: str) -> bool:
        # TODO: voeg protocol-specifieke validatie toe
        return bool(message)