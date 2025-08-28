import copy
import logging
from typing import Any, Dict

from ha_mqtt_pi_smbus.util import deep_merge_dicts, read_yaml


def getConfig(args:Dict[str, Any]) -> Dict[str, Any]:
    config_yaml = None
    secrets_yaml = None
    if args is not None:
        if 'config' in args:
            config_file = args['config']
            config_yaml = read_yaml(config_file)
        if 'secrets' in args:
            secrets_file = args['secrets']
            secrets_yaml = read_yaml(secrets_file)
    merged = deep_merge_dicts(
               deep_merge_dicts(config_yaml, secrets_yaml), args)
    return merged


class DummyConfig:
    def __init__(self):
        pass


class LoggingConfig:
    level:str = None
    def __init__(self):
        pass


class BasicConfig:
    config: str = None
    secrets: str = None
    title: str = None
    subtitle: str = None

    #def __init__(self, args:Dict[str, Any] | object = None):
    #    if args is None:
    #        return
    #    if isinstance(args, BasicConfig):
    #        self.config = args.config
    #        self.secrets = args.secrets
    #        self.title = args.title
    #        self.subtitle = args.subtitle
    #    if 'config' in args:
    #        self.config = args['config']
    #    if 'secrets' in args:
    #        self.secrets = args['secrets']
    #    if 'title' in args:
    #        self.title = args['title']
    #    if 'subtitle' in args:
    #        self.subtitle = args['subtitle']

    def clone(self):
        config = BasicConfig()
        config.config = self.config
        config.secrets = self.secrets
        config.title = self.title
        config.subtitle = self.subtitle
        return config

    def sanitize(self):
        return self


class WebConfig(BasicConfig):
    address: str = None
    port: int = None

    #def __init__(self, args: Dict[str, Any] | BasicConfig = None):
    #    if args is None:
    #        return
    #    if isinstance(args, BasicConfig):
    #        super().__init__(args)
    #        web = args.web
    #        self.address = web.address
    #        self.port = web.port
    #    if 'address' in args:
    #        self.address = args['address']
    #    if 'port' in args:
    #        self.port = args['port']

    def clone(self):
        config = WebConfig()
        config.address = self.address
        config.port = self.port
        return config    

    def sanitize(self):
        return self


class MqttConfig(WebConfig):
    broker: str = 'localhost'
    port: int = 1883
    username: str = 'me'
    password: str = 'mine'
    polling_interval: int = 3
    qos: int = 0
    disable_retain: bool = True
    retain: bool = False
    auto_discover: bool = True
    expire_after: int = 120
    status_topic: str = 'homeassistant'

    #def __init__(self, args:Dict[str, Any] | BasicConfig = None):
    #    if args is None:
    #        return
    #    if 'broker' in args:
    #        self.broker = args['broker']
    #    if 'port' in args:
    #        self.port = args['port']
    #    if 'username' in args:
    #        self.username = args['username']
    #    if 'password' in args:
    #        self.password = args['password']
    #    if 'polling_interval' in args:
    #        self.polling_interval = args['polling_interval']
    #    if 'qos' in args:
    #        self.qos = args['qos']
    #    if 'disable_retain' in args:
    #        self.disable_retain = args['disable_retain']
    #    if 'retain' in args:
    #        self.retain = args['retain']
    #    if 'auto_discover' in args:
    #        self.auto_discover = args['auto_discover']
    #    if 'expire_after' in args:
    #        self.expire_after = args['expire_after']
    #    if 'status_topic' in args:
    #        self.status_topic = args['status_topic']

    def clone(self):
        config = MqttConfig()
        config.broker = self.broker
        config.port = self.port
        config.username = self.username
        config.password = self.password
        config.polling_interval = self.polling_interval
        config.qos = self.qos
        config.disable_retain = self.disable_retain
        config.retain = self.retain
        config.auto_discover = self.auto_discover
        config.expire_after = self.expire_after
        config.status_topic = self.status_topic
        return config    

    def sanitize(self):
        self.broker = 'broker'
        self.port = 'port'
        self.username = 'username'
        self.password = 'password'
        return self

def dict_to_config(args:Dict[str, Any], config = None) -> Any:
#        super().__init__(merged_config)
#        if merged_config is None or merged_config == {}:
#            return
#        for key,value in merged_config.items():
#            if isinstance(value, dict):
#                setattr
#        if 'web' in merged_config:
#          self.web = WebConfig(merged_config['web'])
#        if 'mqtt' in merged_config:
#            self.mqtt = MqttConfig(merged_config['mqtt'])
    if config is None:
        new_config = Config()
        new_args = getConfig(args)
    else:
        new_config = config
        new_args = args
    for key, value in new_args.items():
        if isinstance(value, dict):
            class_name = key[0].upper() + key[1:] + 'Config'
            if class_name in globals():
                class_obj = globals()[class_name]
            else:
                class_obj = DummyConfig
            setattr(new_config, key, dict_to_config(value, class_obj()))
        else:
            setattr(new_config, key, value)
    return new_config


def to_dict(self):
    new_dict = {}
    for k,v in self.__dict__.items():
        if not isinstance(v, (int, float, str, bool, type(None))):
            new_dict[k] = to_dict(v)
        else:
            new_dict[k] = v
    return new_dict

class Config(BasicConfig):
    def __init__(self, args:Dict[str, Any] = None):
        if args is None:
            return
        merged_config = getConfig(args)
        config = dict_to_config(merged_config)
        for k,v in config.__dict__.items():
            setattr(self, k, v)


    def clone(self):
        config = super().clone()
        if self.web is not None:
            config.web = self.web.clone()
        if self.mqtt is not None:
            config.mqtt = self.mqtt.clone()
        return config    

    def sanitize(self):
        clone = super().sanitize()
        if self.web is not None:
            self.web.sanitize()
        if self.mqtt is not None:
            self.mqtt.sanitize()
        return self
