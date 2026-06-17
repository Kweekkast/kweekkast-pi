from ImageCapturing.Actioners.capture_trigger_observer import ICaptureTriggerObserver
from LoggerComponent.LoggerEnum import MessageSeverity
from LoggerComponent import FileLogger
import StringFormatter 
import cv2

from abc import ABC, abstractmethod

class AbstractImageCapturer(ICaptureTriggerObserver, ABC):
    
    @abstractmethod
    def capture_image():
        pass

    