import argparse
import copy
import logging
import socket
import sys
from typing import Any, Dict
import yaml


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merges two dictionaries.

    Two dict structures will be merged.  Values from dict2 will
    overwrite values from dict1 in case of conflicts, except for
    nested dictionaries, which are recursively merged.

    Parameters
    ----------
    dict1 ; Dict[atr, Any]
    dict2 ; Dict[atr, Any]

    Returns
    -------
    dict

    """
    if not dict1:
        return dict2 if dict2 else {}
    elif not dict2:
        return dict1

    # Start with a copy to avoid modifying original dict1
    merged_dict: Dict[str, Any] = copy.deepcopy(dict1)

    for key, value in dict2.items():
        if (
            key in merged_dict
            and isinstance(merged_dict[key], dict)
            and isinstance(value, dict)
        ):
            # If both values are dictionaries, recursively merge them
            merged_dict[key] = deep_merge_dicts(merged_dict[key], value)
        else:
            # Otherwise, overwrite the value from dict1 with the value from dict2
            merged_dict[key] = value
    return merged_dict


def read_yaml(file_path) -> Dict[str, Any]:
    """
    Read yaml from the file specified by file_path
    """
    logger = logging.getLogger(__name__)
    try:
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError:
        logger.error("Error: File not found: %s", file_path)
        return None
    except yaml.YAMLError as e:
        logger.error("Error parsing YAML: %s", e)
        return None


def auto_int(x) -> int:
    """
    convert a value to an int
    """
    return int(x, 0)


def ipaddress(ip: str):
    """
    convert an ip address to its 32-bit value
    """
    try:
        return socket.inet_aton(ip)
    except OSError as e:
        print(f"Invalid ipaddress ({ip}): {e}")


def configOrCmdParm(
    arg,
    cfg: Dict[str, Any],
    cfg_name: list,
    default: str = None,
    required: bool = False,
) -> str:
    """
    Read yaml from the file specified by file_path
    """
    if arg:
        return arg
    for n in cfg_name:
        if n not in cfg:
            if required:
                print(f"parameter '{' '.join(cfg_name)}' required")
                sys.exit()
            return default
        cfg = cfg[n]
    return cfg

class BasicParser(argparse.ArgumentParser):
    config: str
    secrets: str
    title: str
    subtitle: str

    def __init__(self):
        super().__init__(
            description="Raspberry Pi BME280 Home Assistant MQTT client "
            + "for temperature, pressure and humidity",
            epilog="This  program starts a simple web server which can be "
            + "used to connect /disconnect the MQTT client and "
            + "enable/disable device discovery. Without these 2 "
            + "operations, the device wil not appear in Home Assistant.",
        )
        self.add_argument(
            "-c",
            "--config",
            help="config file name (YAML), default(.config.yaml)"
        )
        self.add_argument(
            "-s",
            "--secrets",
            help="secrets file name (YAML) which is merged with "
            + "and overrides entries in config",
        )
        self.add_argument(
            "-t",
            "--title",
            help="the title for the web management interface"
        )
        self.add_argument(
            "--subtitle",
            help="the subtitle for the web management interface"
        )

    def parse_args(self):
        self.args = super().parse_args()

        # determine config/secrets filenames and read
        self.config = deep_merge_dicts(
            read_yaml(
                self.args.config if self.args.config else '.config.yaml')
            , read_yaml(
                self.args.secrets if self.args.secrets else '.secrets.yaml')
            )

        # determine title/subtitle from command, if supplied, otherwise config
        self.title = self.args.title if self.args.title \
            else self.config['title'] if 'title' in self.config else ""
        self.subtitle = self.args.subtitle if self.args.subtitle \
            else self.config['subtitle'] if 'subtitle' in self.config else ""
        return self.args        


class WebConfig:
    address: str
    port: int

class WebParser(BasicParser):
    def __init__(self):
        super().__init__()
        self.add_argument(
            "-w",
            "--web_address",
            help="The address the web server listens on, default(0.0.0.0)",
            type=ipaddress,
        )
        self.add_argument(
            "-o",
            "--web_port",
            help="The port the web server listens on, default(8088)",
            type=int,
        )

    def parse_args(self):    
        self.args = super().parse_args()

        # get web port/address
        self.web = WebConfig()
        web = self.config['web'] if 'web' in self.config else []
        self.web.port = self.args.web_port if self.args.web_port \
            else web['port'] if 'port' in web else 8080
        self.web.address = self.args.web_address if self.args.web_address \
            else web['address'] if 'address' in web else "0.0.0.0"
        return self.args        

class MQTTConfig:
    broker: str
    port: int
    username: str
    password: str
    polling_interval: int
    qos: int
    disable_retain: bool
    retain: bool
    auto_discover: bool
    expire_after: int

    def __init__(self,
                 broker:str = 'localhost',
                 port:int = 1883,
                 username:str = 'me',
                 password:str = 'mine',
                 polling_interval:int = 1,
                 qos:int = 0,
                 disable_retain:bool = True,
                 retain:bool = False,
                 auto_discover:bool = True,
                 expire_after:int = 119):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.polling_interval = polling_interval
        self.qos = qos
        self.disable_retain = disable_retain
        self.retain = not disable_retain
        self.auto_discover = auto_discover
        self.expire_after = expire_after


class MQTTParser(WebParser):
    def __init__(self):
        super().__init__()
        self.add_argument(
            "-b",
            "--mqtt_broker",
            help="MQTT Broker hostname or address"
        )
        self.add_argument(
            "-n",
            "--mqtt_port",
            help="MQTT Broker port number", type=int
        )
        self.add_argument(
            "-u",
            "--mqtt_username",
            "--username",
            "--user",
            help="MQTT username"
        )
        self.add_argument(
            "-p",
            "--mqtt_password",
            "--password",
            help="MQTT password"
        )
        self.add_argument(
            "-i",
            "--mqtt_polling_interval",
            help="MQTT polling interval to check sensor data",
            type=int,
        )
        self.add_argument(
            "-q",
            "--mqtt_qos",
            help="MQTT Quality of Service (0, 1, 2). Check HA MQTT "
            + "documentation for descrition. Default(0)",
            type=int,
            choices=(0, 1, 2),
        )
        self.add_argument(
            "--mqtt_disable_retain",
            help="MQTT retain policy. Check HA MQTT documentation "
            + "for descrition. Default(true)",
            action="store_false",
        )
        self.add_argument(
            "--mqtt_auto_discover",
            help="perform automatic discovery without web interaction",
            action="store_true",
        )
        self.add_argument(
            "--mqtt_expire_after",
            help="MQTT will mark a device unavailable if not heaard from",
            type=int,
        )

    def parse_args(self):
        self.args = super().parse_args()

        # get MQTT parameters
        self.mqtt = MQTTConfig()
        mqtt = self.config['mqtt'] if 'mqtt' in self.config else []
        self.mqtt.broker = self.args.mqtt_broker if self.args.mqtt_broker \
            else mqtt['broker'] if 'broker' in mqtt else 'localhost'
        self.mqtt.port = self.args.mqtt_port if self.args.mqtt_port \
            else mqtt['port'] if 'port' in mqtt else 1883
        self.mqtt.username = self.args.mqtt_username \
            if self.args.mqtt_username \
                else mqtt['username'] if 'username'in mqtt else None
        self.mqtt.password = self.args.mqtt_password \
            if self.args.mqtt_password \
                else mqtt['password'] if 'password' in mqtt else None
        self.mqtt.polling_interval = self.args.mqtt_polling_interval \
            if self.args.mqtt_polling_interval \
                else mqtt['polling_interval'] if 'polling_interval'in mqtt \
                    else 1
        self.mqtt.qos = self.args.mqtt_qos if self.args.mqtt_qos \
            else mqtt['qos'] if 'qos' in mqtt else 0
        self.mqtt.disable_retain = self.args.mqtt_disable_retain \
            if not self.args.mqtt_disable_retain \
                else mqtt['disable_retain'] if 'disable_retain'in mqtt \
                    else False
        self.mqtt.retain = False if self.mqtt.disable_retain else True
        self.mqtt.auto_discover = self.args.mqtt_auto_discover \
            if self.args.mqtt_auto_discover \
                else mqtt['auto_discover'] if 'auto_discover' in mqtt else False
        self.mqtt.expire_after = self.args_mqtt.expire_after \
            if self.args.mqtt_expire_after \
                else mqtt['expire_after'] if 'expire_after' in mqtt else 120
        return self.args


class Parser(MQTTParser):
    def __init__(self):
        super().__init__()

    def parse_args(self):    
        self.args = super().parse_args()
        return self.args
