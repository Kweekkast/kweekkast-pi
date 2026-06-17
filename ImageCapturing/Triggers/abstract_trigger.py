from ImageCapturing.Triggers.capture_trigger_subject import CaptureTrigger_Subject
from abc import ABC, abstractmethod

class Abstract_Trigger(CaptureTrigger_Subject, ABC):
    
    def __init__(self):
        super().__init__()

    @abstractmethod
    def triggerLoop(self):
        pass