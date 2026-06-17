from abc import ABC, abstractmethod

from kweekkast_core.image_capturing.actioners.capture_trigger_observer import ICaptureTriggerObserver


class AbstractImageCapturer(ICaptureTriggerObserver, ABC):
    @abstractmethod
    def capture_image(self) -> None:
        pass
