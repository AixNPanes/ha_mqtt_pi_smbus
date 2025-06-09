import datetime
import json
import logging
import threading
import time
from typing import Any, Dict

from smbus2 import SMBus

class SMBusDevice(SMBus):
    bus:int = None
    address = None
    last_update:datetime.datetime = datetime.datetime.now()

    def __init__(self, bus:int = 1, address:int = 0x76):
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

class SMBusDevice_Sampler_Thread(threading.Thread):
    def __init__(self, logger:logging.Logger, smbus_device:SMBusDevice, polling_interval:int):
        super().__init__(name='SMBusDevice', daemon=True)
        self.__logger = logger
        self.smbus_device = smbus_device
        self.polling_interval = polling_interval
        self.do_run = True

    def run(self) -> None:
        route = 'SMBusDevice_Sampler_Thread'
        while True:
            for i in range(self.polling_interval):
                if not self.do_run:
                    return
                if i == 0:
                    self.smbus_device.sample()
                time.sleep(1)

if __name__ == '__main__':
    import json
    dev = SMBusDevice(1, 0x76)
    print(dev)

