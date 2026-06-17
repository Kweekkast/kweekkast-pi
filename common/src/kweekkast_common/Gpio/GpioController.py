import json

from kweekkast_common.Subscriber import Subscriber
from kweekkast_common.Gpio.GpioDevice import GpioDeviceType, GpioDevice
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.reading import Reading

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
        GpioDeviceType.PUMP:     {1: 23, 2: 18, 3: 17},
        GpioDeviceType.UV_LAMP:  {1: 6,  2: 16,  3: 29},
        GpioDeviceType.LED_LAMP: {1: 24, 2: 25, 3: 26},
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

                file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                                       f"Pin {pin} ingesteld voor {deviceType.value} {index}")

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
            file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__,
                                   f"Kon pin {pin} niet instellen ({e}); "
                  f"{deviceType.value} {index} draait in simulatiemodus")

    def Notify(self, reading: Reading) -> None:
        if not reading.valid:
            file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__,
                                   f"Ongeldig bericht: {reading.message}")
            return

        try:
            data = json.loads(reading.message)
            deviceType = GpioDeviceType(data["device"])
            index = int(data["index"])
            state = bool(data["state"])
            self.SetPin(deviceType, index, state)
            print("TEST")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__,
                                   f"Kon bericht niet verwerken: {reading.message} ({e})")

    def SetPin(self, deviceType: GpioDeviceType, index: int, state: bool) -> None:
        device = self.devices.get((deviceType, index))
        if not device:
            file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__,
                                   f"Onbekend apparaat: {deviceType.value} {index}")
            return

        device.state = state

        output = self.outputs.get((deviceType, index))
        if output is not None:
            try:
                output.on() if state else output.off()
            except Exception as e:
                file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__,
                                       f"Kon pin {device.pin} niet aansturen ({e}); "
                      f"alleen logisch bijgewerkt")

        file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                               f"{deviceType.value} {index} (pin {device.pin}) → {'AAN' if state else 'UIT'}")

    def Cleanup(self) -> None:
        for output in self.outputs.values():
            try:
                output.close()
            except Exception:
                pass
        self.outputs.clear()
        file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__,
                               f"GPIO opgeruimd")