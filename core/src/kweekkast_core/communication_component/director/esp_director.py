from kweekkast_common.communication_component.director import Director
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.reading import Reading
import json

DEFAULT_INTERVAL_TIME = 30000

class EspDirector(Director):

    def __init__(self, communicator: "Communicator"):
        super().__init__(communicator)

    def HandleReading(self, reading: Reading) -> None:
        if reading.valid:
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__,
                                   f"Bericht ontvangen: {reading.message}")
            self.SendMessage("ACK")
        elif not reading.valid:
            file_logger.logger.log(MessageSeverity.WARNING, self.__class__.__name__,
                                   f"Ongeldig bericht: {reading.message}")
            self.SendMessage("NACK")

    def SendIntializeMessage(self):
        message = json.dumps({
            "type": "init",
            "interval": DEFAULT_INTERVAL_TIME
        })
        print(message)
        self.transmitter.SendMessage(message)
