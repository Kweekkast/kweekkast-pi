from LoggerComponent import StringFormatter
from abc import ABC, abstractmethod

class Abstract_Logger(ABC):

    def Log(self, logSeverity, senderClass, msg):
        formattedString = StringFormatter.FormatLogMessage(logSeverity, senderClass, msg)
        self._write(formattedString)

    @abstractmethod
    def _write(self, formatted_message):
        pass