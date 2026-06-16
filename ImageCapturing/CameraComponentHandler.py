from threading import Thread
from LoggerComponent.LoggerEnum import MessageSeverity
from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger
from ImageCapturing.Actioners.ImageCapturer import ImageCapturer
import time

class CameraComponentHandler():
    def __init__(self, abstractTrigger, cameras):
        self.trigger = abstractTrigger
        self.imageCapturers = []

        for x in range(cameras):
            imageCapturer = ImageCapturer(x)
            self.trigger.AddObserver(imageCapturer)
            self.imageCapturers.append(imageCapturer)
            FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"an imageCapturer was added to the list")



    def run(self):
        thread = Thread(target =self.trigger.triggerLoop, args = ())
        thread.start()

    def ReleaseAllCameras(self):
        for imageCapturer in self.imageCapturers:
            self.trigger.removeObserver(imageCapturer)
            imageCapturer.__del__()
            FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"an imageCapturer was released" )