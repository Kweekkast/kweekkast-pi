from kweekkast_common.file_handling import string_formatter
from kweekkast_common.file_handling import path_creation
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_core.image_capturing.actioners.abstract_image_capturer import AbstractImageCapturer
from kweekkast_core.image_capturing.captured_image import CapturedImage
from datetime import UTC, datetime
from pathlib import Path
import uuid


class CameraImageCapturer(AbstractImageCapturer):

    def __init__(
        self,
        video_capture_device_id: int,
        *,
        module_id: int | None = None,
        image_transmitter=None,
        capture_device=None,
        save_png: bool = True,
        jpeg_quality: int = 80,
        image_size: tuple[int, int] = (640, 480),
        fps: float = 5,
        release_after_capture: bool = True,
    ):
        self._capture_device_id = video_capture_device_id
        self.module_id = module_id if module_id is not None else video_capture_device_id + 1
        self.image_transmitter = image_transmitter
        self.save_png = save_png
        self.jpeg_quality = jpeg_quality
        self.image_size = image_size
        self.fps = fps
        self.release_after_capture = release_after_capture
        self._capture_device = capture_device
        self._owns_capture_device = capture_device is None
        self.IMAGES_DIRECTORY = string_formatter.create_image_directory(self._capture_device_id)

    def _claim_capture_device(self) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("OpenCV is required for camera image capture. Install opencv-python.") from exc

        self._capture_device = cv2.VideoCapture(self._capture_device_id, cv2.CAP_V4L2)
        if not self._capture_device.isOpened():
            self._capture_device.release()
            self._capture_device = cv2.VideoCapture(self._capture_device_id)

        self._capture_device.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self._capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, self.image_size[0])
        self._capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, self.image_size[1])
        self._capture_device.set(cv2.CAP_PROP_FPS, self.fps)

    def notify(self) -> None:
        try:
            captured_image = self.capture_image()
            if self.image_transmitter is not None:
                self.image_transmitter.send_image(captured_image)
            file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"{self} was notified")
        except Exception as exc:
            file_logger.logger.log(
                MessageSeverity.ERROR,
                self.__class__.__name__,
                f"Something went wrong notifying: {self}.\nException: {exc!r}",
            )

    def capture_image(self) -> CapturedImage:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("OpenCV is required for camera image capture. Install opencv-python.") from exc

        directory = Path(self.IMAGES_DIRECTORY)
        captured_at = datetime.now(UTC)
        local_path = None

        try:
            capture_device = self._ensure_capture_device()
            ret, frame = capture_device.read()
            if not ret:
                raise ValueError("Something went wrong. Image could not be captured.")

            if self.save_png:
                new_image_path = f"{self.IMAGES_DIRECTORY}/{string_formatter.datetime_string()}.png"
                dir_msg = path_creation.check_and_create_dir(directory)
                file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, dir_msg)
                cv2.imwrite(new_image_path, frame)
                local_path = new_image_path
                file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"An image was written to {new_image_path}")

            encoded, jpeg_buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
            if not encoded:
                raise ValueError("Something went wrong. Image could not be JPEG encoded.")

            return CapturedImage(
                module_id=self.module_id,
                camera_device_id=self._capture_device_id,
                captured_at=captured_at,
                message_id=uuid.uuid4(),
                jpeg_bytes=jpeg_buffer.tobytes(),
                local_path=local_path,
            )
        finally:
            if self.release_after_capture and self._owns_capture_device:
                self._release_capture_device()

    def _ensure_capture_device(self):
        if self._capture_device is None:
            self._claim_capture_device()
        elif not self._capture_device.isOpened():
            self._release_capture_device()
            self._claim_capture_device()

        return self._capture_device

    def _release_capture_device(self) -> None:
        capture_device = self._capture_device
        if capture_device is not None:
            capture_device.release()
        self._capture_device = None

    def __del__(self) -> None:
        self._release_capture_device()
