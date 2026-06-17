import os
from pathlib import Path

from kweekkast_common import string_formatter
from kweekkast_common.logger_component.abstract_logger import AbstractLogger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.logger_component import console_logger


class FileLogger(AbstractLogger):
    def __init__(self):
        self._setup_log_environment()

    def _write(self, formatted_message: str) -> None:
        try:
            with open(string_formatter.SESSION_LOG_FILE_PATH, "a") as file:
                file.write(formatted_message + "\n")
                file.close()
        except Exception as e:
            console_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__,f"There was an error: {repr(e)}")
            self._setup_log_environment()

    def _setup_log_environment(self) -> None:
        file = Path(string_formatter.SESSION_LOG_FILE_PATH)
        directory = Path(string_formatter.SESSION_LOG_DIRECTORY_PATH)

        if directory.exists() and directory.is_dir():
            dir_msg = "Directory exists, no directory was created."
        else:
            os.makedirs(directory, exist_ok=True)
            dir_msg = "Directory did not exist, a new directory was created."

        if file.exists():
            file_msg = "Log file already exists."
            file_msg_severity = MessageSeverity.ERROR
        else:
            file.touch()
            file_msg = "Log file does not exist yet. File created before first log event."
            file_msg_severity = MessageSeverity.DEV

        super().log(MessageSeverity.DEV, self.__class__.__name__, dir_msg)
        super().log(file_msg_severity, self.__class__.__name__, file_msg)


logger = FileLogger()
