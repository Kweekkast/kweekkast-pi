from ImageCapturing.Actioners.CaptureTrigger_Observer import ICaptureTriggerObserver
from LoggerComponent.LoggerEnum import MessageSeverity
from LoggerComponent import FileLogger
import StringFormatter 
import cv2


class ImageCapturer(ICaptureTriggerObserver):

    def __init__(self, VideoCaptureDeviceID):
        self._captureDeviceID = VideoCaptureDeviceID
        self._claimCaptureDevice()

    def notify(self):
        newImagePath = StringFormatter.createImagePath(self._captureDeviceID) 
        if not self._captureDevice.isOpened():
            self._claimCaptureDevice()
            FileLogger.logger.Log(MessageSeverity.WARNING, __class__.__name__,"Attempted to recapture Device")
            return

        ret, frame = self._captureDevice.read()
        if not ret:
            self._captureDevice.release()
            raise ValueError("something went wrong. Image could not be captured")
        
        cv2.imwrite(newImagePath,frame)
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__," An image was written to" + newImagePath)

    def _claimCaptureDevice(self):
        self._captureDevice = cv2.VideoCapture(self._captureDeviceID)

    def __del__(self):
        self._captureDevice.release()