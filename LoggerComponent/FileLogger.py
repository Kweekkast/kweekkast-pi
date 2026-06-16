from LoggerComponent.Abstract_Logger import Abstract_Logger
import StringFormatter
from LoggerComponent.LoggerEnum import MessageSeverity
from pathlib import Path
import os

class File_Logger(Abstract_Logger):

    def __init__(self):
        self._setupLogEnvironment()

    def _write(self, formatted_message):
        with open(StringFormatter.SessionLogFilePath, "a") as file:
            file.write(formatted_message + "\n")

    def _setupLogEnvironment(self):
        file = Path(StringFormatter.SessionLogFilePath)
        directory = Path(StringFormatter.SessionLogDirectoryPath)

        if directory.exists() and directory.is_dir():
            dir_msg = "Directory exists, no directory was created."
        else:
            os.makedirs(directory, exist_ok=True)
            dir_msg = "Directory did not exist, a new directory was created."

        if file.exists():
            file_msg = "Log file already exists."
            file_msg_severity = MessageSeverity.ERROR
        else:
            f = open(file, "x")
            f.close()
            file_msg = "Log file does not exist yet. File Created Before first log event"
            file_msg_severity = MessageSeverity.DEV
            
        super().Log(MessageSeverity.DEV, __class__.__name__, dir_msg)
        super().Log(file_msg_severity, __class__.__name__, file_msg)