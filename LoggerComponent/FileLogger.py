from LoggerComponent.Abstract_Logger import Abstract_Logger
import StringFormatter
from LoggerComponent.LoggerEnum import MessageSeverity
from pathlib import Path
import os

class File_Logger(Abstract_Logger):

    def __init__(self):
        file = Path(StringFormatter.SessionLogFilePath)
        try:
            if file.is_file():
                raise UserWarning("This file already exists")
            elif file.is_dir():
                raise UserWarning("This is a directory")
            else:
                os.makedirs(StringFormatter.SessionLogDirectoryPath)
                os.path.join(StringFormatter.SessionLogDirectoryPath, StringFormatter.SessionLogfileName)
        except Exception as e:
                self._write(StringFormatter.FormatLogMessage(MessageSeverity.ERROR,self.__class__.__name__,"Something went wrong: " + repr(e)))

        self._write(StringFormatter.FormatLogMessage(MessageSeverity.DEV, self.__class__.__name__,"Successfully created file!"))



    def _write(self, formatted_message):
        with open(StringFormatter.SessionLogFilePath, "a") as file:
            file.write(formatted_message + "\n")