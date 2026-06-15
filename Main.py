from LoggerComponent.ConsoleLogger import Console_Logger
from LoggerComponent.FileLogger import File_Logger
from LoggerComponent.LoggerEnum import MessageSeverity

fileLogger = File_Logger()
consoleLogger = Console_Logger()

fileLogger.Log(MessageSeverity.DEV, fileLogger.__class__.__name__, "this is a test message that should be logged in a file")
consoleLogger.Log(MessageSeverity.DEV, consoleLogger.__class__.__name__, "this is a test message that should be logged in the console")

fileLogger.Log(MessageSeverity.ERROR, fileLogger.__class__.__name__, "this is a test message that should be logged in a file")
consoleLogger.Log(MessageSeverity.ERROR, consoleLogger.__class__.__name__, "this is a test message that should be logged in the console")