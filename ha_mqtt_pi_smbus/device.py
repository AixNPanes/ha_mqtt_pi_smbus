import datetime
from importlib.metadata import version, PackageNotFoundError
import json
import logging
import threading
import time
from typing import Any, Dict, List, Sequence

from smbus2 import SMBus

from ha_mqtt_pi_smbus.environ import getCpuInfo, getOSInfo, getObjectId


class HASensor:
    """Definition for a Home Assistant discoverable sensor

    Parameters
    ----------
    units : str
        The string representing the default units for the device. This
        must be a valid unit type for the associated Home Assistant
        sensor type.
    name : str
        The name of the device. This name will be displayed in Home
        Assistant as the device name. The default is the class name
        converted to lower case, ie. class Temperature(HASensor) has a
        device name of temperature by default.
    device_class : str
        The Home Assistant class of the device. This device class
        describes the type of sensor. The default is the class name
        converted to lower case, ie. class Temperature(HASensor) has a
        device class of temperature by default.

    Note
    ----
    This class should be subclassed and not used directly. The
    subclass name, converted to lower case becomes the device class of
    the sensor, ie. the 'Temperature' class would represent a
    'temperature' sensor. This name must be a valid Home Assistant
    sensor class.

    Example
    -------
    from ha_device import HASensor

    class Temperature(HASensor):
        units = f'{chr(176)}C'
        device_class = 'temperature'
        def __init(self, name:str):
            super.__init(self.units, name = name, device_class = self.device_class)

    class Pressure(HASensor):
        units = 'mbar'
        device_class = 'pressure'
        def __init(self, name:str):
            super.__init(self.units, name = name, device_class = self.device_class)

    class Humidity(HASensor):
        units = '%'
        device_class = 'humidity'
        def __init(self, name:str):
            super.__init(self.units, name = name, device_class = self.device_class)

    In this example the 3 sensors for a Bosch BME280 are defined.

    """

    class Availability:     # mutually exclusive with availability_topic
        def __init__(self):
            self.payload_available = 'Available'
            self.payload_unavailable = 'Unavailable'
            #topic:str = None       # set by HASensor.__init__()
            self.value_template = '{{ value_json.availability }}'
            pass
    
    def __init__(
            self,
            units: str,
            name: str = None,
            basename:str = 'homeassistant',
            device_class: str = None,
            expire_after:int = 120,
            state_topic:str = None, 
            ):
        self.diagnostic = False
        self.name = name
        if self.name is None:
            self.name = type(self).__name__.lower()
        self.device_class = device_class
        self.basename = basename
        if self.device_class is None:
            self.device_class = type(self).__name__.lower()
        self.unique_id = f'{name}_{device_class}'
        self.availability = self.Availability()
        self.availability.topic = f'{basename}/{name}/availability'
        self.undiscovery_payload = {
            'platform': 'sensor'
            }
        self.discovery_payload = {
            'platform': 'sensor',
            'device_class': device_class,
            'unique_id': self.unique_id,
            'expire_after': expire_after,
            'unit_of_measurement': units,
            'value_template': f'{{{{ value_json.{self.device_class} }}}}',
            'availability': self.availability.__dict__,
            }

    def jsonPayload(self) -> str:
        return json.dumps(self.discovery_payload, default=vars)


class HADiagnosticSensor(HASensor):
    def __init__(self, name:str = None, device_class:str = None):
        super().__init__(None, name=name, device_class=device_class)
        self.unique_id = f'{name}_diagnostic'
        self.diagnostic = True
        del self.discovery_payload['device_class']
        del self.discovery_payload['unit_of_measurement']
        self.discovery_payload['unique_id'] = self.unique_id
        self.discovery_payload['value_template'] = "{{ value_json.status ~ ' — ' ~ value_json.cpu_temperature ~ '°C' }}"
        self.discovery_payload['entity_category'] = 'diagnostic'
        self.discovery_payload['name'] = 'diagnostic'
        self.discovery_payload['json_attributes_topic'] = f'{name}/diagnostics/state'
        self.discovery_payload['json_attributes_template'] = '{"Status": "{{ value_json.status }}", "CPU Temperature": "{{ value_json.cpu_temperature }}", "Version": "{{ value_json.version }}"}'
        self.discovery_payload['state_topic'] = f'{name}/diagnostics/state'


class HADevice:
    """Definition for a Home Assistant device with discoverable sensors

    This device with its sensors defines that data that is used to see

    Parameters
    ----------
    sensors : List[HASensor]

        The list of sensors defined for the device.

    state_topic : str
        The state topic that will be used in the message to send data to
        Home Assistant. Note that this state topic should be unique for
        each device.
    manufacturer : str
        The name of the manufacturer of the sensor. This will be
        displayed in the Home Assistant detail for the device. For the
        Bosch BME280 sensor, this would be 'Bosch'.
    model : str
        The name of the model of the sensor. This will be displayed in
        the Home Assistant detail for the device. For the Bosch BME280
        sensor, this would be 'BME280'.
    base_name : str
        The base part of the discovery message. This field must match
        the setting in Home Assistant Settings -> Devices and services
        -> Integrations -> MQTT consiguration section Configure
        -> CONFIGURE MQTT OPTIONS -> Enable discovery [Discovery prefix]

    Note
    ----
    This class is designed to be subclassed and not used directly. The
    subclass must override the getdata() method in order to retrieve data
    from the physical device.

    Example
    -------
    import logging
    from ha_device import HADevice, HASensor
    from smbus_device import SMBusDevice, SMBusDevice_Sampler_Thread

    class Temperature(HASensor):
        def __init(self, name:str):
            super.__init(name, f'{chr(176)}C', 'lvr280/state', 'Bosch', 'BME280')

    class Pressure(HASensor):
        def __init(self, name:str):
            super.__init(name, f'mbar', 'lvr280/state', 'Bosch', 'BME280')

    class Humidity(HASensor):
        def __init(self, name:str):
            super.__init(name, f'%', 'lvr280/state', 'Bosch', 'BME280')

    class BME280_Device(HADevice)
        def __init(self, name:str, smbus_device:SMBusDevice, polling_interval:int):
            super().__init__(name, (Temperature(name), Pressure(name), Humidity(name))
            self.smbus_device = smbus_device
            self.sampler_thread = SMBusDevice_Sampler_Thread(smbus_device, polling_interval)
            self.sampler_thread.start()
        def getdata(self) -> Dict[str, Any]:
            return self.smbus_device.getdata()

    """

    class Origin:#
        name:str                    # 'bla2mqtt'
        sw_version:str              # '2.1'
        #support_url:str             # 'https://bla2mqtt.example.com/support'

    class Device:
        #configuration_url:str       # defined only if set
        #connections:Sequence[str]   #
        #model_id:str                # 'xya'
        #suggested_area:str          #
        hw_version:str              # '1.0rev2'
        identifiers:Sequence[str]   # ['ea334450945afc']
        manufacturer:str            # 'Bla electronics'
        model:str                   # 'xya'
        name:str                    # 'Kitchen'
        serial_number:str           # 'ea334450945afc'
        sw_version:str              # '1.0'

    device = Device()
    origin = Origin()
    state_topic:str
    qos:int
    components:Sequence[HASensor]

    def __init__(
        self,
        sensors:list[HASensor],
        name:str,
        state_topic:str,
        manufacturer:str,
        model:str,
        model_id:str = None,
        suggested_area = None,
        base_name:str = 'homeassistant',
        support_url:str = None, #'http://www.example.com',
        qos:int = 0,
    ):
        try:
            __version__ = version("ha_mqtt_pi_smbus")
        except PackageNotFoundError:
             __version__ = "0.0.0"
        basename = base_name
        self.diagnosticSensor = HADiagnosticSensor(name)
        self.sensors = sensors + [self.diagnosticSensor]
        self.origin.name = 'HA MQTT Pi'
        self.origin.sw_version = __version__
        self.origin.support_url = 'http://www.example.com'
        self.device.hw_version = getCpuInfo()['cpu']['Model']
        self.device.identifiers = [ name ]
        self.device.name = name
        self.device.manufacturer = manufacturer
        self.device.model = model
        self.device.serial_number = getObjectId()
        self.device.sw_version = '0.0.1'
        self.state_topic = state_topic
        self.qos = qos
        if support_url is not None:
            self.origin.support_url = support_url
        if model_id is not None:
            self.device.model_id = model_id
        if suggested_area is not None:
            self.origin.suggested_area = suggested_area
        self.discovery_payload = {
                "device": self.device.__dict__,
                "origin": self.origin.__dict__,
                "components": {v.unique_id: v.discovery_payload for v in self.sensors},
                "state_topic": self.state_topic,
                "qos": self.qos,
                }
        self.undiscovery_payload1 = {
                "device": self.device.__dict__,
                "origin": self.origin.__dict__,
                "components": {v.unique_id: v.undiscovery_payload for v in self.sensors},
                "state_topic": self.state_topic,
                "qos": self.qos,
                }
        self.undiscovery_payload2 = {
                "device": self.device.__dict__,
                "origin": self.origin.__dict__,
                "state_topic": self.state_topic,
                "qos": self.qos,
                }
        self.discovery_topic = f'{basename}/device/{self.device.serial_number}/config'
        self.state_topic = state_topic

    def getdata(self) -> Dict[str, Any]:
        raise Exception(f"Class {self.__class__.__module}.{self.__class__.__name__} needs getdata(self) definition")


# class SMBusDevice(SMBus):
class SMBusDevice:
    bus: int = None
    address = None
    last_update: datetime.datetime = datetime.datetime.now()

    def __init__(self, bus: int = 1, address: int = 0x76):
        """Definition for SMBus device specific to sensors

        Parameters
        ----------
        bus : int
            The number of the SMBus (I2C) bus (1 or 2). The default is 1
        address : int
            The address of the device on the I2C bus. The default is
            118 (0x76).

        Note
        ----
        This class is designed to be subclassed and not used directly.
        The subclass must override the sample() and data() methods in
        order to sample the device data adn return the data to the
        application, respectively.

        Example
        -------
        import datetime
        import bme280
        from smbus2 import SMBus

        class BME280(SMBusDevice):
            last_update = datetime.datetime.now()
            temperature:float = -32.0 * 5.0 / 9.0
            pressure:float = 0.0
            humidity:float = 0.0

            def __init(self, bus:int = 1, address:int = 0x76):
                super().__init__(bus)
                self.bus = bus
                self.address = address
                self._calibration_params =
                    bme280.load_calibration_params(self, self.address)

            def sample(self) -> None:
                super().sample()
                data = bme280.sample(
                    self, self.address, self._calibration_params)
                last_update = datetime.datetime.now()
                self.temperature = data.temperature
                self.pressure = data.pressure
                self.humidity = data.humidity

            def getdata(self) -> Dict[str, Any]:
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

        """
        # super().__init__(bus)
        self.bus = bus
        self.address = address
        self._smbus = SMBus(bus)

    # Override this method
    def sample(self) -> None:
        """sample device, save the data in the object's 'data' variable

        Parameters
        ----------
        None

        Example
        -------

        bme = BME280()
        bme.sample()
        """
        self.last_update = datetime.datetime.now()

    # Override this method return any desired data stored
    # in the 'data' variable as a dict
    def getdata(self) -> Dict[str, Any]:
        """return the previously sampled data to the application

        Parameters
        ----------
        None

        Return : Dict[str, Any]
        ------
        The dictionay containing the data for all the sensors for the
        device.

        Note
        ----

        This method should be overriden as the provided data only
        provides SMBus parameters and a time stamp but no actual
        sensor data.

        Example
        -------

        bme = BME280()
        bme.sample()
        data = bme.getdata()
        """
        return {
            "last_update": self.last_update.strftime("%m/%d/%Y %H:%M:%S"),
            "bus": self.bus,
            "address": self.address,
        }

    # Override this method if desired
    def toJson(self) -> str:
        return ""

    # Override this method if desired
    def __str__(self) -> str:
        return f"bus: {self.bus}, address: {self.address}"


class SMBusDevice_Sampler_Thread(threading.Thread):
    def __init__(self, smbus_device: SMBusDevice, polling_interval: int):
        """Definition of a sampler thread for an SMBusDevice

        Parameters
        ----------
        smbus_device : SMBusDevice
            The SMBusDevice which is going to be sampled
        polling_interval : in
            The interval at which polling is to take place

        Note
        ----
        This class is designed to be used in the class which implements
        the HADevice interface. It need not be overriden.

        Example
        -------
        class BME280_Device(HASensor)
            def __init__(self, name:str, smbus_device: SMBusDevice,
                    polling_interval:int)
                super().__init((Temperature(name), Pressure(name), Humidity(name)))
                self.smbus_device = smbus_device
                self.sampler_thread = SMBusDevice_Sampler_Thread(
                    logger, smbus_device, polling_interval)
                self.sampler_thread.start()
        """
        super().__init__(name="SMBusDevice", daemon=True)
        self.__logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.smbus_device = smbus_device
        self.polling_interval = polling_interval
        self.do_run = True

    def run(self) -> None:
        """the thread execution method

        Parameters
        ----------
        None

        Note
        ----

        This method need not be overridden in normal use. It is called
        when the thread is started with the thread.start() method.
        (See class example, above.)
        """
        time.sleep(10) # Wait for startup to get device data out sooner.
        while True:
            for i in range(self.polling_interval):
                if not self.do_run:
                    return
                if i == 0:
                    self.smbus_device.sample()
                time.sleep(1)
