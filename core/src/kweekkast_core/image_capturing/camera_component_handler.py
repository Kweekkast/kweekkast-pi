from threading import Thread
import json
import os

from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_core.image_capturing.actioners.camera_image_capturer import CameraImageCapturer


_ENV_SENTINEL = object()


class CameraComponentHandler:
    def __init__(self, abstract_trigger, cameras: int, *, image_transmitter=None, camera_module_map: dict[int, int] | None = None):
        self._trigger = abstract_trigger
        self._image_capturers = []
        resolved_camera_module_map = camera_module_map or load_camera_module_map()

        for camera_id in range(cameras):
            try:
                image_capturer = CameraImageCapturer(
                    camera_id,
                    module_id=resolved_camera_module_map.get(camera_id, camera_id + 1),
                    image_transmitter=image_transmitter,
                )
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


def load_camera_module_map(raw_value=_ENV_SENTINEL) -> dict[int, int]:
    raw_value = os.environ.get("KWEEK_CAMERA_MODULE_MAP") if raw_value is _ENV_SENTINEL else raw_value
    if not raw_value:
        return {0: 1, 1: 2, 2: 3}

    parsed = json.loads(raw_value)
    if not isinstance(parsed, dict):
        raise ValueError("KWEEK_CAMERA_MODULE_MAP must be a JSON object.")

    return {int(camera_id): int(module_id) for camera_id, module_id in parsed.items()}
