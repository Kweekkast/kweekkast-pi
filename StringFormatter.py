import datetime

def createImagePath(ImageCaptureDevice):
    imagePath = "Assets/Device_" + str(ImageCaptureDevice) + "/" + fetchCustomDateString() + ".png"
    return imagePath

def fetchCustomDateString():
    time_Format = "%Y-%m-%d %H-%M-%S-%f"
    
    date = datetime.datetime.now()
    customDatetimeString = str(date.strftime(time_Format[:-3]))
    return str(customDatetimeString)

def FormatLogMessage(logSeverity, senderClass, msg):
        timestamp = fetchCustomDateString()
        return f"{timestamp}: {logSeverity.name}: {senderClass}: {msg}"

SessionLogDirectoryPath = "logs/"
SessionLogfileName = "log_session_" + fetchCustomDateString() + ".txt"
SessionLogFilePath = SessionLogDirectoryPath + SessionLogfileName