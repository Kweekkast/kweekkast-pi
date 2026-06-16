from enum import Enum


class GpioDeviceType(Enum):
    PUMP = "pump"
    UV_LAMP = "uv_lamp"
    DAY_LAMP = "day_lamp"


class GpioDevice:
    def __init__(self, deviceType: GpioDeviceType, index: int, pin: int):
        self.deviceType = deviceType
        self.index = index
        self.pin = pin
        self.state = False

    def __repr__(self) -> str:
        return f"GpioDevice({self.deviceType.value}, index={self.index}, pin={self.pin}, state={self.state})"