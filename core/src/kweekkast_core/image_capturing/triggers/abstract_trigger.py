from abc import ABC, abstractmethod

from kweekkast_core.image_capturing.triggers.capture_trigger_subject import CaptureTriggerSubject


class AbstractTrigger(CaptureTriggerSubject, ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def trigger_loop(self) -> None:
        pass
