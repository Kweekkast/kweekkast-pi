from kweekkast_common.communication_component.director import Director
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.reading import Reading


class PiDirector(Director):

    def __init__(self, communicator: "Communicator"):
        super().__init__(communicator)

    def HandleReading(self, reading: Reading) -> None:
        if reading.valid:
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"Bericht ontvangen: {reading.message}")
            self.SendMessage(reading.message)
        elif not reading.valid:
            # TODO: error bericht eventueel maken
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"Ongeldig bericht: {reading.message}")
