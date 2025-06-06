import json
from environ import CpuInfo, OSInfo, MacAddress

class HADevice:
    def __init__(self, name:str, units:str, state_topic:str, manufacturer:str, model:str, base_name:str=None):
        self.name = name
        basename = base_name
        if basename == None:
            basename = 'homeassistant'
        cpu = CpuInfo().info['cpu']
        osinfo = OSInfo().info
        device_class = type(self).__name__.lower()
        value_name = name.lower()
        mac_address = MacAddress.get()
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

    def topic(self):
        return self.config_topic

    def payload(self):
        return self.config_payload

    def jsonPayload(self):
        return json.dumps(self.config_payload, default=vars)

    def data(self):
        raise Exception('Class needs data(self) definition')

class HASensor:
    def __init__(self, devices:list):
        mac_address = MacAddress.get()
        self.devices = {}
        dev = None
        for device in devices:
            self.devices[device.discovery_payload['name'].lower()] = device
            dev = device
        self.device_names = list(self.devices.keys())
        self.discovery_topics = {k: v.discovery_topic for k, v in self.devices.items()}
        self.discovery_payload = {k: v.discovery_payload for k, v in self.devices.items()}
        self.state_topic = self.devices[self.device_names[0]].state_topic
