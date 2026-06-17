from threading import Thread
from LoggerComponent.LoggerEnum import MessageSeverity
from LoggerComponent import FileLogger
from ImageCapturing.Actioners.camera_image_capturer import ImageCapturer

class CameraComponentHandler():
    def __init__(self, abstract_trigger, cameras):
        self._TRIGGER = abstract_trigger
        self._IMAGE_CAPTURERS = []

        for x in range(cameras):
            imageCapturer = ImageCapturer(x)
            self._TRIGGER.AddObserver(imageCapturer)
            self._IMAGE_CAPTURERS.append(imageCapturer)
            FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"an imageCapturer was added to the list")

    def run(self):
        thread = Thread(target =self._TRIGGER.triggerLoop, args = ())
        thread.start()

    def release_all_cameras(self):
        for image_capturer in self._IMAGE_CAPTURERS:
            self._TRIGGER.removeObserver(image_capturer)
            image_capturer.__del__()
            FileLogger.logger.Log(MessageSeverity.DEV, __class__.__name__,"an imageCapturer was released" )