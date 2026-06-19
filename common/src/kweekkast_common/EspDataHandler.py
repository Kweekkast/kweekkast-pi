from __future__ import annotations
import json

from kweekkast_common.communication_component.Subscriber import Subscriber
from kweekkast_common.Gpio.GpioController import GpioController
from kweekkast_common.Gpio.GpioDevice import GpioDeviceType
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.reading import Reading


class EspDataHandler(Subscriber):
    """
    Ontvangt data van ESP-communicators.
    - type "control" → stuurt GpioController aan
    - type "sensor"  → stuurt door naar Pi-communicator
    """

    # Mapping van JSON veldnamen naar GpioDeviceType
    DEVICE_MAP = {
        "pump": GpioDeviceType.PUMP,
        "day":  GpioDeviceType.LED_LAMP,
        "grow": GpioDeviceType.UV_LAMP,
    }

    def __init__(self, distributer, gpioController: GpioController):
        self.distributer    = distributer
        self.gpioController = gpioController

    def Notify(self, reading: Reading) -> None:
        if not reading.valid:
            file_logger.logger.log(MessageSeverity.WARNING, self.__class__.__name__,
                                   f"Ongeldig bericht: {reading.message}")
            return

        try:
            data = json.loads(reading.message)
            messageType = data.get("type")

            if messageType == "control":
                self.HandleControl(data)
            elif messageType == "sensor":
                self.HandleSensor(reading, data)
            else:
                file_logger.logger.log(MessageSeverity.WARNING, self.__class__.__name__,
                                       f"Onbekend type: {messageType}")

        except (json.JSONDecodeError, KeyError) as e:
            file_logger.logger.log(MessageSeverity.ERROR, self.__class__.__name__,
                                   f"Kon bericht niet verwerken: {reading.message} ({e})")

    def HandleControl(self, data: dict) -> None:
        """Verwerkt kastbesturing en stuurt GPIO-pinnen aan."""
        for module in data.get("modules", []):
            moduleId = int(module["id"])

            for fieldName, deviceType in self.DEVICE_MAP.items():
                if fieldName in module:
                    state = module[fieldName] == "on"
                    self.gpioController.SetPin(deviceType, moduleId, state)

                    file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                                           f"Module {moduleId} {fieldName} → {'AAN' if state else 'UIT'}")

    def HandleSensor(self, reading: Reading, data: dict) -> None:
        """Stuurt sensordata door naar de Pi-communicator."""
        piCommunicator = self.distributer.FindPiCommunicator()
        if piCommunicator and piCommunicator.director:
            file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                                   f"Sensordata doorsturen naar Pi: {reading.message}")
            piCommunicator.director.HandleReading(reading)
        else:
            file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                                   "Geen Pi gevonden om sensordata naar door te sturen")