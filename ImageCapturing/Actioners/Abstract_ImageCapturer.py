from ImageCapturing.Actioners.CaptureTrigger_Observer import ICaptureTriggerObserver
from LoggerComponent.LoggerEnum import MessageSeverity
from LoggerComponent import FileLogger
import StringFormatter 
import cv2

from abc import ABC, abstractmethod

class Abstract_ImageCapturer(ICaptureTriggerObserver, ABC):
    
    @abstractmethod
    def captureImage():
        pass

    