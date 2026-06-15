from threading import Thread
from ImageCapturing.CameraComponentHandler import CameraComponentHandler
from ImageCapturing.Triggers.TimerTrigger import TimerTrigger

cameraComponentHandler = CameraComponentHandler(TimerTrigger(60))
thread = Thread(target =cameraComponentHandler.run(), args = ())
thread.start()



