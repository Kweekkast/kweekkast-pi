from threading import Thread
from ImageCapturing.Actioners.ImageCapturer import ImageCapturer

class CameraComponentHandler():
    def __init__(self, abstractTrigger, cameras):
        self.trigger = abstractTrigger

        for x in range(cameras):
            imageCapturer = ImageCapturer(x)
            self.trigger.AddObserver(imageCapturer)



    def run(self):
        thread = Thread(target =self.trigger.triggerLoop(), args = ())
        thread.start()
        