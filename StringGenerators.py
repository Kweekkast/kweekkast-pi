import datetime

def createImagePath(ImageCaptureDevice):
    imagePath = "Assets/Device_" + str(ImageCaptureDevice) + "/" + fetchCustomDateString() + ".png"
    return imagePath

def fetchCustomDateString():
    date = datetime.datetime.now()
    customDatetimeString = (
        str(date.strftime("%d")) + 
        "_" + str(date.strftime("%m")) + 
        "_" + str(date.strftime("%Y")) + 
        "-" + str(date.strftime("%H")) + 
        "_" + str(date.strftime("%M")))
    return customDatetimeString