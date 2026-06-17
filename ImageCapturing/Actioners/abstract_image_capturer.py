from ImageCapturing.Actioners.capture_trigger_observer import ICaptureTriggerObserver
import cv2

from abc import ABC, abstractmethod

class AbstractImageCapturer(ICaptureTriggerObserver, ABC):
    
    @abstractmethod
    def capture_image():
        pass

    