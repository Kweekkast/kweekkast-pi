from abc import ABC, abstractmethod

from kweekkast_common import string_formatter


class AbstractLogger(ABC):
    def log(self, log_severity, sender_class: str, message: str) -> None:
        formatted_string = string_formatter.format_log_message(log_severity, sender_class, message)
        self._write(formatted_string)

    @abstractmethod
    def _write(self, formatted_message: str) -> None:
        pass
