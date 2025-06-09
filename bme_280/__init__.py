import datetime
from typing import Any, Dict

import bme280
from smbus2 import SMBus

class SMBusDevice(SMBus):
    bus:int = None
    address = None
    last_update:datetime.datetime = datetime.datetime.now()

    def __ini__(self, bus:int = 1, address:int = 0x76):
       super().__init__(bus)
       self.bus = bus
       self.address = address

    # Override this method
    def sample(self) -> None:
        self.last_update = datetime.datetime.now()

    # Override this method
    def data(self) -> Dict[str, Any]:
        return {
                "last_update": self.last_update.strftime('%m/%d/%Y %H:%M:%S'),
                "bus": self.bus,
                "address": self.address,
                }

    # Override this method if desired
    def toJson() -> str:
        return ""

    # Override this method if desired
    def __str__(self) -> str:
        return f"bus: {self.bus}, address: {self.address}"

class BME_280(SMBusDevice):
    temperature:float = -32.0 * 5 / 9
    pressure:float = 0.0
    humidity:float = 0.0

    def __init__(self, bus:int = 1, address:int = 0x76):
        super().__init__(bus)
        self.bus = bus
        self.address = address
        self._calibration_params = bme280.load_calibration_params(self, self.address)

    def sample(self) -> None:
        super().sample()
        data = bme280.sample(self, self.address, self._calibration_params)
        self.temperature = data.temperature
        self.pressure = data.pressure
        self.humidity = data.humidity

    def data(self) -> Dict[str, Any]:
        return {
                "last_update": self.last_update.strftime('%m/%d/%Y %H:%M:%S'),
                "bus": self.bus,
                "address": self.address,
                "temperature": round(self.temperature, 1),
                "pressure": round(self.pressure, 1),
                "humidity": round(self.humidity, 1),
                }

if __name__ == '__main__':
    import json
    bme = BME_280()
    print(bme)
    bme.sample()
    print(bme.data())

