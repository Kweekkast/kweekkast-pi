from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kweekkast_common.communicator import Communicator

from kweekkast_common.director.director import Director
from kweekkast_common.reading import Reading


class EspDirector(Director):

    def __init__(self, communicator: "Communicator"):
        super().__init__(communicator)

    def HandleReading(self, reading: Reading) -> None:
        if reading.valid:
            print(f"[EspDirector] Bericht ontvangen: {reading.message}")
            self.SendMessage("ACK")
        elif not reading.valid:
            print(f"[EspDirector] Ongeldig bericht: {reading.message}")
            self.SendMessage("NACK")