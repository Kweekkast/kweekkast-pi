from threading import Thread
from ImageCapturing.Actioners.ImageCapturer import ImageCapturer

class CameraComponentHandler():
    def __init__(self, abstractTrigger, cameras):
        self.trigger = abstractTrigger
        self.imageCapturers = []

        for x in range(cameras):
            imageCapturer = ImageCapturer(x)
            self.trigger.AddObserver(imageCapturer)
            self.imageCapturers.append(imageCapturer)



    def run(self):
        thread = Thread(target =self.trigger.triggerLoop(), args = ())
        thread.start()
        time.sleep(300)
        self.ReleaseAllCameras()


    def ReleaseAllCameras(self):
        for imageCapturer in self.imageCapturers:
            self.trigger.removeObserver(imageCapturer)
            imageCapturer.__del__()
        