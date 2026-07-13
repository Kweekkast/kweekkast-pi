from threading import Thread
import os

from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_core.image_capturing.actioners.camera_image_capturer import CameraImageCapturer


_ENV_SENTINEL = object()
DEFAULT_CAMERA_DEVICE_IDS = [0, 2, 4]


class CameraComponentHandler:
    def __init__(
        self,
        abstract_trigger,
        *,
        image_transmitter=None,
        camera_device_ids: list[int] | None = None,
    ):
        self._trigger = abstract_trigger
        self._image_capturers = []
        resolved_camera_device_ids = (
            list(camera_device_ids)
            if camera_device_ids is not None
            else load_camera_device_ids()
        )

        for module_index, camera_id in enumerate(resolved_camera_device_ids, start=1):
            try:
                image_capturer = CameraImageCapturer(
                    camera_id,
                    module_id=module_index,
                    image_transmitter=image_transmitter,
                    fps=float(os.environ.get("KWEEK_CAMERA_FPS", "5")),
                )
                self._trigger.add_observer(image_capturer)
                self._image_capturers.append(image_capturer)
                file_logger.logger.log(
                    MessageSeverity.DEV,
                    self.__class__.__name__,
                    f"Image capturer toegevoegd voor /dev/video{camera_id} -> module {module_index}",
                )
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


def load_camera_device_ids(raw_value=_ENV_SENTINEL) -> list[int]:
    raw_value = os.environ.get("KWEEK_CAMERA_DEVICE_IDS") if raw_value is _ENV_SENTINEL else raw_value
    if not raw_value:
        return list(DEFAULT_CAMERA_DEVICE_IDS)

    device_ids = [int(part.strip()) for part in raw_value.split(",") if part.strip()]
    if not device_ids:
        raise ValueError("KWEEK_CAMERA_DEVICE_IDS must contain at least one camera device id.")
    if len(set(device_ids)) != len(device_ids):
        raise ValueError("KWEEK_CAMERA_DEVICE_IDS must not contain duplicates.")
    if any(device_id < 0 for device_id in device_ids):
        raise ValueError("KWEEK_CAMERA_DEVICE_IDS must contain non-negative integers.")

    return device_ids
