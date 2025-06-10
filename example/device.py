import logging
from typing import Any, Dict

import bme280

from ha_device import HADevice, HASensor
from smbus_device import SMBusDevice, SMBusDevice_Sampler_Thread

class Temperature(HASensor):
    def __init__(self, sensor_name:str):
        super().__init__(sensor_name, f'{chr(176)}C', "bme280/state", "Bosch", "BME280")

class Pressure(HASensor):
    def __init__(self, sensor_name:str):
        super().__init__(sensor_name, "mbar", "bme280/state", "Bosch", "BME280")

class Humidity(HASensor):
    def __init__(self, sensor_name:str):
        super().__init__(sensor_name, "%", "bme280/state", "Bosch", "BME280")

class BME280_Device(HADevice):
    def __init__(self, logger:logging.Logger, name:str, smbus_device:SMBusDevice, polling_interval:int):
        super().__init__((Temperature(name), Pressure(name), Humidity(name)))
        route = 'BME280_Sensor'
        self.__logger = logger
        self.smbus_device = smbus_device
        self.sampler_thread = SMBusDevice_Sampler_Thread(logger, smbus_device, polling_interval)
        self.sampler_thread.start()

    def data(self) -> Dict[str, Any]:
        route = 'BME280_Sensor'
        return self.smbus_device.data()

class BME280(SMBusDevice):
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
                "temperature_units": f'{chr(176)}C',
                "pressure": round(self.pressure, 1),
                "pressure_units": "mbar",
                "humidity": round(self.humidity, 1),
                "humidity_units": "%",
                }

if __name__ == '__main__':
    import json
    dev = BME280(1, 0x76)
    print(f'BME280 device: {dev}')
    dev.sample()
    print(f'device sample: {dev.data()}')

