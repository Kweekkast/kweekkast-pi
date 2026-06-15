import datetime

def createImagePath(ImageCaptureDevice):
    imagePath = "Assets/Device_" + str(ImageCaptureDevice) + "/" + fetchCustomDateString() + ".png"
    return imagePath

def fetchCustomDateString():
    time_Format = "%Y-%m-%d %H-%M-%S-%f"
    
    date = datetime.datetime.now()
    customDatetimeString = str(date.strftime(time_Format))
    return str(customDatetimeString)