import argparse
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
    merged_dict: Dict[str, Any] = (
        dict1.copy()
    )  # Start with a copy to avoid modifying original dict1

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
        socket.inet_aton(ip)
        return ip
    except OSError as e:
        print(f"Invalid ipaddress ({ip}): {e}")


def configOrCmdParm(
    arg,
    config: Dict[str, Any],
    secrets: Dict[str, Any],
    cfg_name: list,
    default: str = None,
    required: bool = False,
) -> str:
    """
    Read yaml from the file specified by file_path
    """
    if arg:
        return arg
    cfg = deep_merge_dicts(config, secrets)
    for n in cfg_name:
        if n not in cfg:
            if required:
                print(f"parameter '{' '.join(cfg_name)}' required")
                sys.exit()
            return default
        cfg = cfg[n]
    return cfg


class Parser:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Raspberry Pi BME280 Home Assistant MQTT client "
            + "for temperature, pressure and humidity",
            epilog="This  program starts a simple web server which can be "
            + "used to connect /disconnect the MQTT client and "
            + "enable/disable device discovery. Without these 2 "
            + "operations, the device wil not appear in Home Assistant.",
        )
        parser.add_argument(
            "-t", "--title", help="the title for the web management interface"
        )
        parser.add_argument(
            "--subtitle", help="the subtitle for the web management interface"
        )
        parser.add_argument(
            "-w",
            "--web_address",
            help="The address the web server listens on, default(0.0.0.0)",
            type=ipaddress,
        )
        parser.add_argument(
            "-o",
            "--web_port",
            help="The port the web server listens on, default(8088)",
            type=int,
        )
        parser.add_argument(
            "-b", "--mqtt_broker", help="MQTT Broker hostname or address"
        )
        parser.add_argument(
            "-n", "--mqtt_port", help="MQTT Broker port number", type=int
        )
        parser.add_argument(
            "-u", "--mqtt_username", "--username", "--user", help="MQTT username"
        )
        parser.add_argument("-p", "--mqtt_password", "--password", help="MQTT password")
        parser.add_argument(
            "-i",
            "--mqtt_polling_interval",
            help="MQTT polling interval to check sensor data",
            type=int,
        )
        parser.add_argument(
            "-q",
            "--mqtt_qos",
            help="MQTT Quality of Service (0, 1, 2). Check HA MQTT "
            + "documentation for descrition. Default(0)",
            type=int,
            choices=(0, 1, 2),
        )
        parser.add_argument(
            "--mqtt_disable_retain",
            help="MQTT retain policy. Check HA MQTT documentation "
            + "for descrition. Default(true)",
            action="store_false",
        )
        parser.add_argument(
            "--mqtt_auto_discover",
            help="perform automatic discovery without web interaction",
            action="store_true",
        )
        parser.add_argument(
            "--mqtt_expire_after",
            help="MQTT will mark a device unavailable if not heaard from",
            type=int,
        )
        parser.add_argument(
            "-a",
            "--bme280_address",
            help="BME280 address (118, 119, 0x67, 0x77",
            type=auto_int,
            choices=(118, 119),
        )
        parser.add_argument(
            "-r",
            "--bme280_bus",
            help="BME280 I2C bus (1, 2)",
            type=int, choices=(1, 2)
        )
        parser.add_argument(
            "-N",
            "--bme280_sensor_name",
            help="BME280 Home Assistant sensor name",
            type=str,
        )
        parser.add_argument(
            "-I", "--bme280_polling_interval", help="BME280 polling interval", type=int
        )
        parser.add_argument(
            "-c", "--config", help="config file name (YAML), default(.config.yaml)"
        )
        parser.add_argument(
            "-s",
            "--secrets",
            help="secrets file name (YAML) which is merged with "
            + "and overrides entries in config",
        )

        args = parser.parse_args()

        # determine config/secrets filename and read it
        if args.config:
            config_file = args.config
        else:
            config_file = ".config.yaml"
        config = read_yaml(config_file)
        if args.secrets:
            secrets_file = args.secrets
        else:
            secrets_file = ".secrets.yaml"
        config = read_yaml(config_file)
        secrets = read_yaml(secrets_file)

        # determine title and subtitle from command, if supplied, otherwise config
        if args.title:
            self.title = args.title
        elif "title" in config:
            self.title = config["title"]
        else:
            self.title = ""
        if args.subtitle:
            self.subtitle = args.subtitle
        elif "subtitle" in config:
            self.subtitle = config["subtitle"]
        else:
            self.subtitle = ""

        # get MQTT parameters
        self.mqtt = {}
        self.mqtt["broker"] = configOrCmdParm(
            args.mqtt_broker, config, secrets, ["mqtt", "broker"], default="localhost"
        )
        self.mqtt["port"] = configOrCmdParm(
            args.mqtt_port, config, secrets, ["mqtt", "port"], default=1883
        )
        self.mqtt["username"] = configOrCmdParm(
            args.mqtt_username, config, secrets, ["mqtt", "username"]
        )
        self.mqtt["password"] = configOrCmdParm(
            args.mqtt_password, config, secrets, ["mqtt", "password"]
        )
        self.mqtt["polling_interval"] = configOrCmdParm(
            args.mqtt_password, config, secrets, ["mqtt", "polling_interval"], default=1
        )
        self.mqtt["qos"] = configOrCmdParm(
            args.mqtt_qos, config, secrets, ["mqtt", "qos"], default=0
        )
        self.mqtt["disable_retain"] = configOrCmdParm(
            args.mqtt_disable_retain if not args.mqtt_disable_retain else None,
            config,
            secrets,
            ["mqtt", "disable_retain"],
        )
        self.mqtt["auto_discover"] = configOrCmdParm(
            args.mqtt_auto_discover,
            config,
            secrets,
            ["mqtt", "auto_discover"],
        )
        self.mqtt["retain"] = False if self.mqtt["disable_retain"] else True
        self.mqtt["expire_after"] = configOrCmdParm(
            args.mqtt_qos, config, secrets, ["mqtt", "expire_after"],
            default=120
        )
        # get BME280 parameters
        self.bme280 = {}
        self.bme280["bus"] = configOrCmdParm(
            args.bme280_bus, config, secrets, ["bme280", "bus"], default=1
        )
        self.bme280["address"] = configOrCmdParm(
            args.bme280_address, config, secrets, ["bme280", "address"], default=0x76
        )
        self.bme280["sensor_name"] = configOrCmdParm(
            args.bme280_address, config, secrets, ["bme280", "sensor_name"]
        )
        self.bme280["polling_interval"] = configOrCmdParm(
            args.bme280_address,
            config,
            secrets,
            ["bme280", "polling_interval"],
            default=60,
        )

        # get web parameters
        self.web = {}
        self.web["port"] = configOrCmdParm(
            args.web_port, config, secrets, ["web", "port"], default=8088
        )
        self.web["address"] = configOrCmdParm(
            args.web_address, config, secrets, ["web", "address"], default="0.0.0.0"
        )
