from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Esp32.Communicator import Communicator

from Esp32.Director.Director import Director
from Esp32.Reading import Reading
from Esp32.Transmitter.Transmitter import Transmitter


class PiDirector(Director):

    def __init__(self, communicator: "Communicator", transmitter: Transmitter):
        super().__init__(communicator, transmitter)

    # def HandleReading(self, reading: Reading) -> None:
    #     if reading.valid:
    #         print(f"[PiDirector] Bericht ontvangen: {reading.message}")
    #         # TODO: verwerk de data
    #     else:
    #         print(f"[PiDirector] Ongeldig bericht genegeerd: {reading.message}")