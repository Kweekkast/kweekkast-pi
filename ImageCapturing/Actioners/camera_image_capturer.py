from ImageCapturing.Actioners.abstract_image_capturer import AbstractImageCapturer
from LoggerComponent.LoggerEnum import MessageSeverity
from LoggerComponent import FileLogger
import StringFormatter 
import cv2


class CameraImageCapturer(AbstractImageCapturer):

    def __init__(self, VideoCaptureDeviceID):
        self._CAPTURE_DEVICE_ID = VideoCaptureDeviceID
        self._claim_capture_device()

    def _claim_capture_device(self):
        self._CAPTURE_DEVICE = cv2.VideoCapture(self._CAPTURE_DEVICE_ID)

    def notify(self):
        try:
            self.capture_image()
            FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__, str(self) + " was notified")
        except Exception as e:
            FileLogger.logger.Log(MessageSeverity.ERROR, __class__.__name__, "Something went wrong notifying:" + str(self) + ". \n Exception:" + repr(e))

    def capture_image(self):
        new_image_path = StringFormatter.createImagePath(self._CAPTURE_DEVICE_ID) 
        if not self._CAPTURE_DEVICE.isOpened():
            self._claim_capture_device()
            FileLogger.logger.Log(MessageSeverity.WARNING, __class__.__name__,"Attempted to recapture Device")

        ret, frame = self._CAPTURE_DEVICE.read()
        if not ret:
            self._CAPTURE_DEVICE.release()
            raise ValueError("something went wrong. Image could not be captured")
    
        cv2.imwrite(new_image_path,frame)
        FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__," An image was written to" + new_image_path)

    def __del__(self):
        self._CAPTURE_DEVICE.release()