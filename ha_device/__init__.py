import json
from typing import Any, Dict, List

from environ import getCpuInfo, getOSInfo, getMacAddress

class HASensor:
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

    def data(self) -> Dict[str, Any]:
        raise Exception('Class needs data(self) definition')

class HADevice:
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
