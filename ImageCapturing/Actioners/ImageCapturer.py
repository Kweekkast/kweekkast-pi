from ImageCapturing.Actioners.CaptureTrigger_Observer import ICaptureTriggerObserver
import StringGenerators 
import cv2

class ImageCapturer(ICaptureTriggerObserver):

    def __init__(self, VideoCaptureDeviceID):
        self._captureDeviceID = VideoCaptureDeviceID

    def notify(self):
        captureDevice = cv2.VideoCapture(self._captureDeviceID)
        ret, frame = captureDevice.read()
        if not ret:
            raise ValueError("something went wrong. Image could not be captured")
        
        cv2.imwrite(StringGenerators.createImagePath(self._captureDeviceID),frame)
        captureDevice.release()