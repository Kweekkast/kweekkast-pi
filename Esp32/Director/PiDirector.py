from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Esp32.Communicator import Communicator

from Esp32.Director.Director import Director
from Esp32.Reading import Reading


class PiDirector(Director):

    def __init__(self, communicator: "Communicator"):
        super().__init__(communicator)

    def HandleReading(self, reading: Reading) -> None:
        if reading.valid:
            print(f"[EspDirector] Bericht ontvangen: {reading.message}")
            self.SendMessage(reading.message)
        elif not reading.valid:
    # TODO: error bericht eventueel maken
            print(f"[EspDirector] Ongeldig bericht: {reading.message}")