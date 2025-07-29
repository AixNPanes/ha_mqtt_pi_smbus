import datetime
import logging
from typing import Any, Dict

import bme280

from ha_mqtt_pi_smbus.device import (
    HADevice,
    HASensor,
    SMBusDevice,
    SMBusDevice_Sampler_Thread,
)


class Temperature(HASensor):
    units: str = f"{chr(176)}C"
    device_class = "temperature"

    def __init__(self, sensor_name: str = None):
        super().__init__(
            self.units, name=sensor_name, device_class=self.device_class
        )

class Pressure(HASensor):
    units: str = "mbar"
    device_class = "pressure"

    def __init__(self, sensor_name: str = None):
        super().__init__(
            self.units, name=sensor_name, device_class=self.device_class
        )

class Humidity(HASensor):
    units: str = "%"
    device_class = "humidity"

    def __init__(self, sensor_name: str = None):
        super().__init__(
            self.units, name=sensor_name, device_class=self.device_class
        )

class BME280_Device(HADevice):
    """Definition for a Home Assistant dicscoverable sensor device

    Parameters
    ----------
    sensor_name : str
        The name of the device containing the sensor. This name is the
        display name for the device in Home Assistant.
    state_topic : str
        The MQTT state topic that accompanies the sensor data that is
        sent to Home Assistant. The state topic must be unique for each
        device.
    manufacturer : str
        The sensor device's manufacturer name. This name will be
        displayed in the device detail in Home Assistant.
    model : str
        The sensor device's model name. This name will be displayed in
        the device detail in Home Assistant.
    smbus_device : SMBusDivice
        The sensor device's interface object. This object communicates
        with the physical device to retrieve the sensor data.
    polling_interval : int
        The interval at which data will be sampled from the device and
        placed in the device object.

    Example
    -------

    bme280_device = BME280_Device('Living Room TPH')

    """

    def __init__(
        self,
        name: str,
        state_topic: str,
        manufacturer: str,
        model: str,
        smbus_device: SMBusDevice,
        polling_interval: int,
        expire_after: int = 120
    ):
        super().__init__(
            (
                Temperature(),
                Pressure(),
                Humidity(),
            ),
            name,
            state_topic,
            manufacturer,
            model,
            expire_after = expire_after,
        )
        self.__logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.smbus_device = smbus_device
        self.sampler_thread = SMBusDevice_Sampler_Thread(smbus_device, polling_interval)
        self.sampler_thread.start()

    def data(self) -> Dict[str, Any]:
        return self.smbus_device.data()


class BME280(SMBusDevice):
    """Definition for a SMBus device which communicated over I2C

    Parameters
    ----------
    bus : int
        The I2C bus number which is used to connect to the sensor device
        (1 or 2)
    address : int
        The address of the sensor device on the I2C bus. For a BME280
        this is either 0x76(118) or 0x77(119).

    Example
    -------

    bme280 = BME280(bus = 1, address = 0x76)

    """

    last_update: datetime = datetime.datetime.now()
    temperature: float = -32.0 * 5 / 9
    pressure: float = 0.0
    humidity: float = 0.0

    def __init__(self, bus: int = 1, address: int = 0x76):
        super().__init__(bus)
        self.bus = bus
        self.address = address
        self._calibration_params = bme280.load_calibration_params(
            self._smbus, self.address
        )

    def sample(self) -> None:
        """makes one sample of the device

        The sampled data is retained in the device for later collection
        with the data() method.

        Parameters
        ----------
        None

        Example
        -------
        bme280.sample()

        """
        super().sample()
        data = bme280.sample(self._smbus, self.address, self._calibration_params)
        self.last_update = datetime.datetime.now()
        self.temperature = data.temperature
        self.pressure = data.pressure
        self.humidity = data.humidity

    def data(self) -> Dict[str, Any]:
        """returns sampled data

        The data was either sampled previously by the saple() method
        or, alternatively, the initial data stored in the object will
        be returned.

        Parameters
        ----------
        None

        Return
        ------
        A dict structure containing pertinent data.

        """
        return {
            "last_update": self.last_update.strftime("%m/%d/%Y %H:%M:%S"),
            "bus": self.bus,
            "address": self.address,
            "temperature": round(self.temperature, 1),
            "temperature_units": f"{chr(176)}C",
            "pressure": round(self.pressure, 1),
            "pressure_units": "mbar",
            "humidity": round(self.humidity, 1),
            "humidity_units": "%",
        }
