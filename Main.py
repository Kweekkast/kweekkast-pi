from LoggerComponent import ConsoleLogger
from LoggerComponent import FileLogger

from LoggerComponent.LoggerEnum import MessageSeverity


FileLogger.logger.Log(MessageSeverity.DEV, FileLogger.logger.__class__.__name__, "this is a test message that should be logged in a file")
ConsoleLogger.logger.Log(MessageSeverity.DEV, ConsoleLogger.logger.__class__.__name__, "this is a test message that should be logged in the console")

FileLogger.logger.Log(MessageSeverity.DEV, FileLogger.logger.__class__.__name__,"this is a test message that should be logged in a file")
ConsoleLogger.logger.Log(MessageSeverity.DEV, ConsoleLogger.logger.__class__.__name__, "this is a test message that should be logged in the console")