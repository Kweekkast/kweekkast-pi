from ImageCapturing.Triggers.capture_trigger_subject import CaptureTriggerSubject
from abc import ABC, abstractmethod

class AbstractTrigger(CaptureTriggerSubject, ABC):
    
    def __init__(self):
        super().__init__()

    @abstractmethod
    def triggerLoop(self):
        pass