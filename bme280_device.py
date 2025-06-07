import json
import threading
import logging
import time
from environ import CpuInfo, OSInfo, MacAddress
from device import HADevice, HASensor
from bme_280 import BME_280

class BME_280_Sampler_Thread(threading.Thread):
    def __init__(self, logger:logging.Logger, bme280:BME_280, polling_interval:int):
        super().__init__(name='BME280', daemon=True)
        self.__logger = logger
        self.bme280 = bme280
        self.polling_interval = polling_interval
        self.do_run = True

    def run(self):
        route = 'BME_280_Sampler_Thread'
        while True:
            for i in range(self.polling_interval):
                if not self.do_run:
                    return
                if i == 0:
                    self.bme280.sample()
                time.sleep(1)

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
        self.sampler_thread = BME_280_Sampler_Thread(logger, bme280, polling_interval)
        self.sampler_thread.start()

    def data(self):
        route = 'BME280_Sensor'
        return self.bme280.data()
