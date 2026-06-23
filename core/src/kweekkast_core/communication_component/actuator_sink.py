from __future__ import annotations

from typing import Protocol

from kweekkast_common.gpio.gpio_controller import GpioController
from kweekkast_common.gpio.gpio_device import GpioDeviceType
from kweekkast_common.net_core_protocol import ModuleCommand


class ModuleActuatorSink(Protocol):
    def apply(self, commands: list[ModuleCommand]) -> None:
        pass


class GpioModuleActuatorSink:
    OUTPUT_MAP = {
        "pump": GpioDeviceType.PUMP,
        "day": GpioDeviceType.LED_LAMP,
        "grow": GpioDeviceType.UV_LAMP,
    }

    def __init__(self, gpio_controller: GpioController | None = None):
        self.gpio_controller = gpio_controller or GpioController()

    def apply(self, commands: list[ModuleCommand]) -> None:
        for command in commands:
            self.gpio_controller.SetPin(self.OUTPUT_MAP["pump"], command.module_id, command.pump)
            self.gpio_controller.SetPin(self.OUTPUT_MAP["day"], command.module_id, command.day)
            self.gpio_controller.SetPin(self.OUTPUT_MAP["grow"], command.module_id, command.grow)

    def close(self) -> None:
        self.gpio_controller.Cleanup()
