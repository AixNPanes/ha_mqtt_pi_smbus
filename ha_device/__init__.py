import json
from typing import Any, Dict, List

from environ import getCpuInfo, getOSInfo, getMacAddress

class HASensor:
    """ Definition for a Home Assistant discoverable sensor

    Parameters
    ----------
    name : str
        The name of the device. This name will be displayed in Home Assistant as the device name.

    units : str
        The string representing the default units for the device. This must be a valid unit type for the associated Home Assistant sensor type.

    state_topic : str
        The state topic which will be used to send state messaged to Home Assisitant. It generally will look something like 'bme280/state'.

    manufacturer : str
        The name of the manufacturer of the sensor. This will be displayed in the Home Assistant detail for the device. For the Bosch BME280 sensor, this would be 'Bosch'.

    model : str
        The name of the model of the sensor. This will be displayed in the Home Assistant detail for the device. For the Bosch BME280 sensor, this would be 'BME280'.

    base_name : str
        The base part of the discovery message. This field must match the setting in Home Assistant Settings -> Devices and services -> Integrations -> MQTT consiguration section Configure -> CONFIGURE MQTT OPTIONS -> Enable discovery [Discovery prefix]

    Note
    ----
    This class should be subclassed and not used directly. The subclass name, converted to lower case becomes the device class of the sensor, ie. the 'Temperature' class would represent a 'temperature' sensor. This name must be a valid Home Assistant sensor class.

    Example
    -------
    from ha_device import HASensor
    Temperature(HASensor):
        def __init(self, name:str):
            super.__init(name, f'{chr(176)}C', 'lvr280/state', 'Bosch', 'BME280')

    Pressure(HASensor):
        def __init(self, name:str):
            super.__init(name, f'mbar', 'lvr280/state', 'Bosch', 'BME280')

    Humidity(HASensor):
        def __init(self, name:str):
            super.__init(name, f'%', 'lvr280/state', 'Bosch', 'BME280')

    In this example the 3 sensors for a Bosch BME280 are defined. Note that for these 3 sensors in one device, the name, state_topic, manufacturer and model are identical for the three sensors, only the class names and the units are different. For another BME280 sensor, you would choose a different state topic. 

    """
    def __init__(self, name:str, units:str, state_topic:str, manufacturer:str, model:str, base_name:str=None):
        self.name = name
        basename = base_name
        if basename == None:
            basename = 'homeassistant'
        cpu = getCpuInfo()['cpu']
        osinfo = getOSInfo()
        device_class = type(self).__name__.lower()
        value_name = name.lower()
        mac_address = getMacAddress()
        serial = mac_address.replace(":", "")
        unique_id = f'{serial[-6:]}-{value_name}'
        hardware = cpu['Model']
        software = osinfo['PRETTY_NAME']
        self.manufacturer = manufacturer
        self.model = model
        self.state_topic = state_topic
        self.discovery_payload = {
                "name": f'{device_class}',
                "stat_t": self.state_topic,
                "device_class": f'{device_class}',
                "val_tpl": f'{{{{ value_json.{device_class} }}}}',
                "unit_of_meas": f'{units}',
                "uniq_id": f'{unique_id}-{device_class}',
                "dev": {
                    "ids":[f'{name}'],
                    "name": f'{name}',
                    "mf": f'{manufacturer}',
                    "mdl": f'{model}',
                    "sw": f'{software}',
                    "hw": f'{hardware}',
                    "sn": f'{serial}',
                }
            }
        self.discovery_topic = f'{basename}/sensor/{unique_id}-{device_class}/config'

    def topic(self) -> Dict[str, Any]:
        return self.config_topic

    def payload(self) -> Dict[str, Any]:
        return self.config_payload

    def jsonPayload(self) -> str:
        return json.dumps(self.config_payload, default=vars)

class HADevice:
    """ Definition for a Home Assistant device with discoverable sensors

    Parameters
    ----------
    sensors : List[HASensor]

        The list of sensors defined for the device.

    Note
    ----
    This class is designed to be subclassed and not used directly. The subclass must override the data() method in order to retrieve data from the physical device.

    Example
    -------
    import loggin
    from ha_device import HADevice
    from smbus_device import SMBusDevice, SMBusDevice_Sampler_Thread
    Temperature(HASensor):
        def __init(self, name:str):
            super.__init(name, f'{chr(176)}C', 'lvr280/state', 'Bosch', 'BME280')

    Pressure(HASensor):
        def __init(self, name:str):
            super.__init(name, f'mbar', 'lvr280/state', 'Bosch', 'BME280')

    Humidity(HASensor):
        def __init(self, name:str):
            super.__init(name, f'%', 'lvr280/state', 'Bosch', 'BME280')

    BME280_Device(HADevice)
        def __init(self, logger:logging.Logger, name:str, smbus_device:SMBusDevice, polling_interval:int):
            super().__init__(name, (Temperature(name), Pressure(name), Humidity(name))
            self.smbus_device = smbus_device
            self.sampler_thread = SMBus_Sampler_Thread(logger, smbus_device, polling_interval)
            self.sampler_thread.start()
        def data(self) -> Dict[str, Any]:
            return self.smbus_device.data()

    """
    def __init__(self, sensors:List[Dict[str, Any]]):
        mac_address = getMacAddress()
        self.sensors = {}
        _sensor = None
        for sensor in sensors:
            self.sensors[sensor.discovery_payload['name'].lower()] = sensor
            _sensor = sensor
        self.sensor_names = list(self.sensors.keys())
        self.discovery_topics = {k: v.discovery_topic for k, v in self.sensors.items()}
        self.discovery_payload = {k: v.discovery_payload for k, v in self.sensors.items()}
        self.state_topic = self.sensors[self.sensor_names[0]].state_topic

    def data(self) -> Dict[str, Any]:
        raise Exception('Class needs data(self) definition')

