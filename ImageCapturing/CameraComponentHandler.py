from ImageCapturing.Actioners.ImageCapturer import ImageCapturer

class CameraComponentHandler():
    def __init__(self, abstractTrigger):
        self.trigger = abstractTrigger

        self.imageCapturer2 = ImageCapturer(1)
        self.imageCapturer3 = ImageCapturer(2)

        self.trigger.AddObserver(ImageCapturer(0))
        self.trigger.AddObserver(self.imageCapturer2)
        self.trigger.AddObserver(self.imageCapturer3)



    def run(self):
        self.trigger.triggerLoop()