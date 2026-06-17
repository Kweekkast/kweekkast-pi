import datetime

def createImagePath(ImageCaptureDevice):
    imagePath = "Assets/Device_" + str(ImageCaptureDevice) + "/" + fetchCustomDateString() + ".png"
    return imagePath

def fetchCustomDateTimeString():
    time_Format = "%Y-%m-%d %H-%M-%S-%f"
    
    date = datetime.datetime.now()
    customDatetimeString = str(date.strftime(time_Format[:-3]))
    return str(customDatetimeString)

def fetchCustomDateString():
    time_Format = "%Y-%m-%d"
    
    date = datetime.datetime.now()
    customDatetimeString = str(date.strftime(time_Format[:-3]))
    return str(customDatetimeString)

def fetchCustomTimeString():
    time_Format = "%H-%M-%S-%f"
    
    date = datetime.datetime.now()
    customDatetimeString = str(date.strftime(time_Format[:-3]))
    return str(customDatetimeString)

def FormatLogMessage(logSeverity, senderClass, msg):
        timestamp = fetchCustomDateTimeString()
        return f"{timestamp}: {logSeverity.name}: {senderClass}: {msg}"

SessionLogDirectoryPath = "logs/" + fetchCustomDateString() + "/"
SessionLogfileName = "log_session_" + fetchCustomTimeString() + ".txt"
SessionLogFilePath = SessionLogDirectoryPath + SessionLogfileName