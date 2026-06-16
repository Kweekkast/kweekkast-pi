import json
from Esp32.Reading import Reading
from Esp32.Connection.Connection import ConnectionDevice
from Esp32.Broker.Subscriber import Subscriber
from Esp32.Gpio.GpioDevice import GpioDevice, GpioDeviceType

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[GpioController] RPi.GPIO niet beschikbaar, simulatiemodus actief")


class GpioController(Subscriber):
    """
    Subscribet op ConnectionDevice.PI topic via de broker.
    Verwacht JSON: {"device": "pump", "index": 1, "state": true}

    Pinnen (BCM):
      Pompen:          index 1=17, 2=27, 3=22
      UV lampen:       index 1=5,  2=6,  3=13
      Daglicht lampen: index 1=19, 2=26, 3=21
    """

    PIN_MAP: dict[GpioDeviceType, dict[int, int]] = {
        GpioDeviceType.PUMP:     {1: 17, 2: 27, 3: 22},
        GpioDeviceType.UV_LAMP:  {1: 5,  2: 6,  3: 13},
        GpioDeviceType.DAY_LAMP: {1: 19, 2: 26, 3: 21},
    }

    def __init__(self):
        self.devices: dict[tuple, GpioDevice] = {}
        self.SetupPins()

    def SetupPins(self) -> None:
        for deviceType, indices in self.PIN_MAP.items():
            for index, pin in indices.items():
                device = GpioDevice(deviceType, index, pin)
                self.devices[(deviceType, index)] = device
                if GPIO_AVAILABLE:
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.LOW)
                print(f"[GpioController] Pin {pin} ingesteld voor {deviceType.value} {index}")

    def Notify(self, reading: Reading) -> None:
        if not reading.valid:
            print(f"[GpioController] Ongeldig bericht: {reading.message}")
            return

        try:
            data = json.loads(reading.message)
            deviceType = GpioDeviceType(data["device"])
            index = int(data["index"])
            state = bool(data["state"])
            self.SetPin(deviceType, index, state)
            print("TEST")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[GpioController] Kon bericht niet verwerken: {reading.message} ({e})")

    def SetPin(self, deviceType: GpioDeviceType, index: int, state: bool) -> None:
        device = self.devices.get((deviceType, index))
        if not device:
            print(f"[GpioController] Onbekend apparaat: {deviceType.value} {index}")
            return

        device.state = state

        if GPIO_AVAILABLE:
            GPIO.output(device.pin, GPIO.HIGH if state else GPIO.LOW)

        print(f"[GpioController] {deviceType.value} {index} (pin {device.pin}) → {'AAN' if state else 'UIT'}")

    def Cleanup(self) -> None:
        if GPIO_AVAILABLE:
            GPIO.cleanup()
        print("[GpioController] GPIO opgeruimd")