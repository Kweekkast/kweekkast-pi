import json

from kweekkast_common.Subscriber import Subscriber
from kweekkast_common.Gpio.GpioDevice import GpioDeviceType, GpioDevice
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.reading import Reading

try:
    from gpiozero import OutputDevice
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[GpioController] gpiozero niet beschikbaar, simulatiemodus actief")


class GpioController(Subscriber):
    """
    Verwacht JSON:
    {
      "type": "control",
      "modules": [
        {"id": 1, "pump": "on", "day": "off", "grow": "off"},
        {"id": 2, "pump": "off", "day": "on", "grow": "off"}
        {"id": 3, "pump": "off", "day": "on", "grow": "off"}
      ]
    }

    Pinnen (BCM):
      Pompen:          index 1=23, 2=18, 3=17
      UV lampen:       index 1=6,  2=16, 3=29
      Daglicht lampen: index 1=24, 2=25, 3=26
    """

    PIN_MAP: dict[GpioDeviceType, dict[int, int]] = {
        GpioDeviceType.PUMP:     {1: 23, 2: 18, 3: 17},
        GpioDeviceType.UV_LAMP:  {1: 6,  2: 16, 3: 29},
        GpioDeviceType.LED_LAMP: {1: 24, 2: 25, 3: 26},
    }

    # Mapping van JSON veldnaam → GpioDeviceType
    FIELD_MAP: dict[str, GpioDeviceType] = {
        "pump": GpioDeviceType.PUMP,
        "grow": GpioDeviceType.UV_LAMP,
        "day":  GpioDeviceType.LED_LAMP,
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

            if data.get("type") != "control":
                file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__,
                                       f"Onbekend type: {data.get('type')}")
                return

            for module in data.get("modules", []):
                moduleId = int(module["id"])

                for field, deviceType in self.FIELD_MAP.items():
                    if field in module:
                        state = module[field] == "on"
                        self.SetPin(deviceType, moduleId, state)

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
        file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__, "GPIO opgeruimd")