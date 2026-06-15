from ImageCapturing.Actioners.ImageCapturer import ImageCapturer

class CameraComponentHandler():
    def __init__(self, abstractTrigger):
        self.trigger = abstractTrigger

        imageCapturer1 = ImageCapturer(0)
        self.trigger.AddObserver(imageCapturer1)
        imageCapturer2 = ImageCapturer(1)
        self.trigger.AddObserver(imageCapturer2)
        imageCapturer3 = ImageCapturer(2)
        self.trigger.AddObserver(imageCapturer3)



    def run(self):
        self.trigger.triggerLoop()