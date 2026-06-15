from ImageCapturing.CameraComponentHandler import CameraComponentHandler
from ImageCapturing.Triggers.TimerTrigger import TimerTrigger

cameraComponentHandler = CameraComponentHandler(TimerTrigger(30),1)
cameraComponentHandler.run()




