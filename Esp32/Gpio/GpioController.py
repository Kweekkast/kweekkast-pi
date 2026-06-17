import json
from Esp32.Reading import Reading
from Esp32.Connection.Connection import ConnectionDevice
from Esp32.Broker.Subscriber import Subscriber
from Esp32.Gpio.GpioDevice import GpioDevice, GpioDeviceType

# gpiozero gebruikt op de Pi 5 de lgpio-backend en werkt daar wel betrouwbaar,
# in tegenstelling tot RPi.GPIO dat voor de oudere Broadcom-chip is geschreven.
# We vangen hier niet alleen ImportError op, maar ook eventuele runtime-fouten
# die tijdens het instellen van een pin kunnen optreden (bv. een ontbrekende
# of kapotte GPIO-backend), zodat de simulatiemodus altijd een werkend vangnet is.
try:
    from gpiozero import OutputDevice
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[GpioController] gpiozero niet beschikbaar, simulatiemodus actief")


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
        self.outputs: dict[tuple, "OutputDevice"] = {}
        self.SetupPins()

    def SetupPins(self) -> None:
        for deviceType, indices in self.PIN_MAP.items():
            for index, pin in indices.items():
                device = GpioDevice(deviceType, index, pin)
                self.devices[(deviceType, index)] = device

                if GPIO_AVAILABLE:
                    self.TrySetupOutput(deviceType, index, pin)

                print(f"[GpioController] Pin {pin} ingesteld voor {deviceType.value} {index}")

    def TrySetupOutput(self, deviceType: GpioDeviceType, index: int, pin: int) -> None:
        """
        Probeert een OutputDevice aan te maken voor deze pin. Als dat om
        welke reden dan ook faalt (bv. backend niet beschikbaar, pin al
        in gebruik), valt deze ene pin terug op simulatiemodus zonder de
        rest van de setup te blokkeren.
        """
        global GPIO_AVAILABLE
        try:
            self.outputs[(deviceType, index)] = OutputDevice(pin, initial_value=False)
        except Exception as e:
            print(f"[GpioController] Kon pin {pin} niet instellen ({e}); "
                  f"{deviceType.value} {index} draait in simulatiemodus")

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

        output = self.outputs.get((deviceType, index))
        if output is not None:
            try:
                output.on() if state else output.off()
            except Exception as e:
                print(f"[GpioController] Kon pin {device.pin} niet aansturen ({e}); "
                      f"alleen logisch bijgewerkt")

        print(f"[GpioController] {deviceType.value} {index} (pin {device.pin}) → {'AAN' if state else 'UIT'}")

    def Cleanup(self) -> None:
        for output in self.outputs.values():
            try:
                output.close()
            except Exception:
                pass
        self.outputs.clear()
        print("[GpioController] GPIO opgeruimd")