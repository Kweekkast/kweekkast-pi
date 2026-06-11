from ImageCapturing.Actioners.CaptureTrigger_Observer import ICaptureTriggerObserver
import StringGenerators 
import cv2

class ImageCapturer(ICaptureTriggerObserver):

    def __init__(self, VideoCaptureDeviceID):
        self._captureDeviceID = VideoCaptureDeviceID
        self._captureDevice = cv2.VideoCapture(self._captureDeviceID)

    def notify(self):

        ret, frame = self._captureDevice.read()
        if not ret:
            raise ValueError("something went wrong. Image could not be captured")
        
        cv2.imwrite(StringGenerators.createImagePath(self._captureDeviceID),frame)