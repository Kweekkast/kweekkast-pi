import threading

from kweekkast_common.communication_component.connection import Connection
from kweekkast_common.communication_component.director import Director
from kweekkast_common.reading import Reading
from kweekkast_common.communication_component.receiver import Receiver
from kweekkast_common.subject import Subject


class Communicator(Subject):

    def __init__(self, connection: Connection):
        super().__init__()
        self.connection = connection
        self.reading = Reading()

        self.director = Director.CreateDirector(self)

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
