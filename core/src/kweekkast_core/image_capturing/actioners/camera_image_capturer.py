from kweekkast_common import string_formatter
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_core.image_capturing.actioners.abstract_image_capturer import AbstractImageCapturer


class CameraImageCapturer(AbstractImageCapturer):
    def __init__(self, video_capture_device_id: int):
        self._capture_device_id = video_capture_device_id
        self._claim_capture_device()

    def _claim_capture_device(self) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("OpenCV is required for camera image capture. Install opencv-python.") from exc

        self._capture_device = cv2.VideoCapture(self._capture_device_id)

    def notify(self) -> None:
        try:
            self.capture_image()
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"{self} was notified")
        except Exception as exc:
            file_logger.logger.log(
                MessageSeverity.ERROR,
                self.__class__.__name__,
                f"Something went wrong notifying: {self}.\nException: {exc!r}",
            )

    def capture_image(self) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("OpenCV is required for camera image capture. Install opencv-python.") from exc

        new_image_path = string_formatter.create_image_path(self._capture_device_id)
        if not self._capture_device.isOpened():
            self._claim_capture_device()
            file_logger.logger.log(MessageSeverity.WARNING, self.__class__.__name__, "Attempted to recapture device")

        ret, frame = self._capture_device.read()
        if not ret:
            self._capture_device.release()
            raise ValueError("Something went wrong. Image could not be captured.")

        cv2.imwrite(new_image_path, frame)
        file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"An image was written to {new_image_path}")

    def __del__(self) -> None:
        capture_device = getattr(self, "_capture_device", None)
        if capture_device is not None:
            capture_device.release()
