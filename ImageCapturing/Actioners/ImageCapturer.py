from ImageCapturing.Actioners.CaptureTrigger_Observer import ICaptureTriggerObserver
from LoggerComponent.LoggerEnum import MessageSeverity
from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger
import StringGenerators 
import cv2


class ImageCapturer(ICaptureTriggerObserver):

    def __init__(self, VideoCaptureDeviceID):
        self._captureDeviceID = VideoCaptureDeviceID
        self._captureDevice = cv2.VideoCapture(self._captureDeviceID)

    def notify(self):
        newImagePath = StringGenerators.createImagePath(self._captureDeviceID) 
        ret, frame = self._captureDevice.read()
        if not ret:
            raise ValueError("something went wrong. Image could not be captured")
        
        cv2.imwrite(newImagePath,frame)
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__," An image was written to" + newImagePath)

    def __del__(self):
        self._captureDevice.release()