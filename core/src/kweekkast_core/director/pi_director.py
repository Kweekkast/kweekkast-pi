from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kweekkast_common.communicator import Communicator

from kweekkast_common.director.director import Director
from kweekkast_common.reading import Reading


class PiDirector(Director):

    def __init__(self, communicator: "Communicator"):
        super().__init__(communicator)

    def HandleReading(self, reading: Reading) -> None:
        if reading.valid:
            print(f"[PiDirector] Bericht ontvangen: {reading.message}")
            self.SendMessage(reading.message)
        elif not reading.valid:
    # TODO: error bericht eventueel maken
            print(f"[PiDirector] Ongeldig bericht: {reading.message}")
