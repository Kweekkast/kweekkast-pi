from __future__ import annotations
from typing import TYPE_CHECKING

from LoggerComponent.LoggerEnum import MessageSeverity
from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger

if TYPE_CHECKING:
    from kweekkast_common.communicator import Communicator

from kweekkast_common.director.director import Director
from kweekkast_common.reading import Reading


class PiDirector(Director):

    def __init__(self, communicator: "Communicator"):
        super().__init__(communicator)

    def HandleReading(self, reading: Reading) -> None:
        if reading.valid:
            FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,f"Bericht ontvangen: {reading.message}")
            self.SendMessage(reading.message)
        elif not reading.valid:
    # TODO: error bericht eventueel maken
            FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,f"Ongeldig bericht: {reading.message}")