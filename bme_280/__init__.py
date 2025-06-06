import bme280
from smbus2 import SMBus
import datetime

class BME_280:
    port: int = None
    address = None
    bus: SMBus = None
    temperature: float = -32.0 * 5 / 9
    pressure: float = 0.0
    humidity: float = 0.0
    last_update: datetime.datetime = datetime.datetime.now()

    def __init__(self, port: int = 1, address=0x76):
        self.port = port
        self.address = address
        self.bus = SMBus(port)
        self._calibration_params = bme280.load_calibration_params(self.bus, self.address)

    def sample(self):
        data = bme280.sample(self.bus, self.address, self._calibration_params)
        self.temperature = data.temperature
        self.pressure = data.pressure
        self.humidity = data.humidity
        self.last_update = datetime.datetime.now()

    def data(self):
        return {
                "last_update": self.last_update.strftime('%m/%d/%Y %H:%M:%S'),
                "port": self.port,
                "address": self.address,
                "temperature": round(self.temperature, 1),
                "pressure": round(self.pressure, 1),
                "humidity": round(self.humidity, 1),
                }

    def toJson():
        return ""

    def __str__(self):
        return f"port: {self.port}, address: {self.address}"

if __name__ == '__main__':
    import json
    bme = BME_280()
    bme.sample()
    print(json.dumps(bme, indent=4))

