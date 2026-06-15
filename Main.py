
from timeit import Timer
from threading import Thread

from ImageCapturing.Triggers.TimerTrigger import TimerTrigger
from ImageCapturing.Triggers.Buttontrigger import ButtonTrigger
from ImageCapturing.Actioners.ImageCapturer import ImageCapturer

cameraComponentHandler = CameraComponentHandler(TimerTrigger)
cameraComponentHandler.run()

trigger = TimerTrigger(60) #TimerTrigger(60) for timer trigger, ButtonTrigger() for button trigger
thread = Thread(target =trigger.triggerLoop, args = ())
thread.start()
imageCapturer1 = ImageCapturer(0)
trigger.AddObserver(imageCapturer1)
imageCapturer2 = ImageCapturer(1)
trigger.AddObserver(imageCapturer2)
imageCapturer3 = ImageCapturer(2)
trigger.AddObserver(imageCapturer3)









