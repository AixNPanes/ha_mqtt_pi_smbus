import logging
from typing import Any, Dict

from environ import CpuInfo, OSInfo, MacAddress
from ha_device import HADevice, HASensor
from smbus_device import SMBusDevice, SMBusDevice_Sampler_Thread
from bme_280 import BME_280

class Temperature(HASensor):
    def __init__(self, sensor_name:str):
        super().__init__(sensor_name, f'{chr(176)}C', "tph280/state", "Bosch", "BME280")

class Pressure(HASensor):
    def __init__(self, sensor_name:str):
        super().__init__(sensor_name, "mbar", "tph280/state", "Bosch", "BME280")

class Humidity(HASensor):
    def __init__(self, sensor_name:str):
        super().__init__(sensor_name, "%", "tph280/state", "Bosch", "BME280")

class BME280_Device(HADevice):
    def __init__(self, logger:logging.Logger, name:str, bme280:BME_280, polling_interval:int):
        super().__init__((Temperature(name), Pressure(name), Humidity(name)))
        route = 'BME280_Sensor'
        self.__logger = logger
        self.bme280 = bme280
        self.sampler_thread = SMBusDevice_Sampler_Thread(logger, bme280, polling_interval)
        self.sampler_thread.start()

    def data(self) -> Dict[str, Any]:
        route = 'BME280_Sensor'
        return self.bme280.data()
