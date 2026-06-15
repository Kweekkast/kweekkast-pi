from threading import Thread
from ImageCapturing.Actioners.ImageCapturer import ImageCapturer
import StringGenerators
import time

class CameraComponentHandler():
    def __init__(self, abstractTrigger, cameras):
        self.trigger = abstractTrigger
        self.imageCapturers = []

        for x in range(cameras):
            imageCapturer = ImageCapturer(x)
            self.trigger.AddObserver(imageCapturer)
            self.imageCapturers.append(imageCapturer)
            print(StringGenerators.fetchCustomDateString() + ": CameraComponentHandler: an imageCapturer was added to the list")



    def run(self):
        thread = Thread(target =self.trigger.triggerLoop, args = ())
        thread.start()

        print(StringGenerators.fetchCustomDateString() + ": CameraComponentHandler: System Sleeping for 5 minutes")
        time.sleep(300)
        print(StringGenerators.fetchCustomDateString() + ": CameraComponentHandler: System is done sleeping Sleeping")
        self.ReleaseAllCameras()


    def ReleaseAllCameras(self):
        for imageCapturer in self.imageCapturers:
            self.trigger.removeObserver(imageCapturer)
            imageCapturer.__del__()
            print(StringGenerators.fetchCustomDateString() + ": CameraComponentHandler: an imageCapturer was released" )