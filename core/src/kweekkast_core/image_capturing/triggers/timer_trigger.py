import time

from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_core.image_capturing.triggers.abstract_trigger import AbstractTrigger


class TimerTrigger(AbstractTrigger):
    def __init__(self, sleep_time_seconds: float):
        super().__init__()
        self._sleep_time_seconds = sleep_time_seconds

    def trigger_loop(self) -> None:
        file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, "The trigger loop has started")
        while True:
            start_time_seconds = time.time()

            super().notify_all_observers()

            seconds_elapsed = time.time() - start_time_seconds
            recalculated_sleep_time_seconds = max(0, self._sleep_time_seconds - seconds_elapsed)

            file_logger.logger.log(
                MessageSeverity.DEV,
                self.__class__.__name__,
                f"Notifying all observers took: {seconds_elapsed} seconds",
            )
            file_logger.logger.log(
                MessageSeverity.DEV,
                self.__class__.__name__,
                f"Sleeping {recalculated_sleep_time_seconds} seconds before notifying observers again",
            )

            time.sleep(recalculated_sleep_time_seconds)
