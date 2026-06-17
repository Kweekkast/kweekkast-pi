from kweekkast_common.logger_component import console_logger, file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity


class CaptureTriggerSubject:
    def __init__(self):
        self._observer_list = []

    def add_observer(self, new_observer) -> None:
        if not hasattr(new_observer, "notify"):
            raise TypeError("Observer must implement notify()")

        self._observer_list.append(new_observer)
        file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, "Observer was added to list")

    def remove_observer(self, old_observer) -> None:
        self._observer_list.remove(old_observer)
        file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, "Observer was removed from list")

    def notify_all_observers(self) -> None:
        file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, "Notifying all observers")

        for observer in self._observer_list:
            try:
                observer.notify()
                file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, "An observer was notified")
            except Exception as exc:
                file_logger.logger.log(
                    MessageSeverity.ERROR,
                    self.__class__.__name__,
                    f"Something went wrong notifying: {observer}.\nException: {exc!r}",
                )
                continue

        file_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, "All observers were notified")
        console_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, "All observers were notified")
