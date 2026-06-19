import os
from pathlib import Path
from kweekkast_common.file_handling import path_creation
from kweekkast_common.file_handling import string_formatter
from kweekkast_common.logger_component.abstract_logger import AbstractLogger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.logger_component import console_logger

SESSION_LOG_DIRECTORY_PATH = f"logs/{string_formatter.date_only_string()}/"
SESSION_LOG_FILE_NAME = f"log_session_{string_formatter.time_only_string()}.txt"
SESSION_LOG_FILE_PATH = SESSION_LOG_DIRECTORY_PATH + SESSION_LOG_FILE_NAME


class FileLogger(AbstractLogger):
    def __init__(self):
        self._setup_log_environment()

    def _write(self, formatted_message: str) -> None:
        try:
            with open(SESSION_LOG_FILE_PATH, "a") as file:
                file.write(formatted_message + "\n")
                file.close()
        except Exception as e:
            console_logger.logger.log(MessageSeverity.DEV, self.__class__.__name__, f"There was an error: {repr(e)}")
            self._setup_log_environment()

    def _setup_log_environment(self) -> None:
        file = Path(SESSION_LOG_DIRECTORY_PATH)
        directory = Path(SESSION_LOG_DIRECTORY_PATH)

        dir_msg = path_creation.check_and_create_dir(directory)
        file_msg = path_creation.check_and_create_file(file)

        super().log(MessageSeverity.DEV, self.__class__.__name__, dir_msg)
        super().log(MessageSeverity.DEV, self.__class__.__name__, file_msg)


logger = FileLogger()
