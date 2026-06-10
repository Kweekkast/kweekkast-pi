
from ImageCapturing.Triggers.TimerTrigger import TimerTrigger
from ImageCapturing.Actioners.ImageCapturer import ImageCapturer


trigger = TimerTrigger(600)
imageCapturer1 = ImageCapturer(0)
imageCapturer2 = ImageCapturer(1)
imageCapturer3 = ImageCapturer(2)

trigger.AddObserver(imageCapturer1)
trigger.AddObserver(imageCapturer2)
trigger.AddObserver(imageCapturer3)

trigger.triggerLoop()




