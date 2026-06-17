from threading import Thread

from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_core.image_capturing.actioners.camera_image_capturer import CameraImageCapturer


class CameraComponentHandler:
    def __init__(self, abstract_trigger, cameras: int):
        self._trigger = abstract_trigger
        self._image_capturers = []

        for camera_id in range(cameras):
            try:
                image_capturer = CameraImageCapturer(camera_id)
                self._trigger.add_observer(image_capturer)
                self._image_capturers.append(image_capturer)
                file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, "An image capturer was added")
            except Exception as exc:
                file_logger.logger.log(
                    MessageSeverity.ERROR,
                    self.__class__.__name__,
                    f"Something went wrong: {exc!r}",
                )

    def run(self) -> None:
        thread = Thread(target=self._trigger.trigger_loop, daemon=True)
        thread.start()

    def release_all_cameras(self) -> None:
        for image_capturer in self._image_capturers:
            self._trigger.remove_observer(image_capturer)
            image_capturer.__del__()
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, "An image capturer was released")
