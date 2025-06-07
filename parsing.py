import re
import time
import json
import yaml
import logging
import random
import sys
import argparse
import socket

def deep_merge_dicts(dict1, dict2):
    """
    Recursively merges two dictionaries.
    Values from dict2 will overwrite values from dict1 in case of conflicts,
    except for nested dictionaries, which are recursively merged.
    """
    merged_dict = dict1.copy()  # Start with a copy to avoid modifying original dict1

    for key, value in dict2.items():
        if key in merged_dict and isinstance(merged_dict[key], dict) and isinstance(value, dict):
            # If both values are dictionaries, recursively merge them
            merged_dict[key] = deep_merge_dicts(merged_dict[key], value)
        else:
            # Otherwise, overwrite the value from dict1 with the value from dict2
            merged_dict[key] = value
    return merged_dict


def read_yaml(file_path):
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError:
        logger.error(f"Error: File not found: {file_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML: {e}")
        return None

loglevels = logging.getLevelNamesMapping()
lognames = ', '.join(list(loglevels.keys()))

def auto_int(x):
    return int(x,0)

def ipaddress(ip:str):
    try:
        socket.inet_aton(ip)
        return ip
    except OSError as e:
        print(f'Invalid ipaddress ({ip}): {e}')

def configOrCmdParm(arg, config:dict, secrets:dict, cfg_name:list, default:str = None, required: bool = False) -> str:
    if arg:
        return arg
    cfg = deep_merge_dicts(config, secrets)
    for n in cfg_name:
        if not n in cfg:
            if required:
                print(f"parameter '{' '.join(cfg_name)}' required")
                sys.exit()
            return default
        cfg = cfg[n]
    return cfg    

class Parser:
    def __init__(self):
        parser = argparse.ArgumentParser(
                description="Raspberry Pi BME280 Home Assistant MQTT client for temperature, pressure and humidity",
                epilog = "This  program starts a simple web server which can be used to connect /disconnect the MQTT client and enable/disable device discovery. Without these 2 operations, the device wil not appear in Home Assistant."
                )
        parser.add_argument("-l", "--loglevel", help=f"logging level ({lognames})")
        parser.add_argument("-w", "--web_address", help="The address the web server listens on, default(0.0.0.0)", type=ipaddress)
        parser.add_argument("-o", "--web_port", help="The port the web server listens on, default(8088)", type=int)
        parser.add_argument("-b", "--mqtt_broker", help="MQTT Broker hostname or address")
        parser.add_argument("-n", "--mqtt_port", help="MQTT Broker port number", type=int)
        parser.add_argument("-u", "--mqtt_username", "--username", "--user", help="MQTT username")
        parser.add_argument("-p", "--mqtt_password", "--password", help="MQTT password")
        parser.add_argument("-i", "--mqtt_polling_interval", help="MQTT polling interval to check sensor data", type=int)
        parser.add_argument("-a", "--bme280_address", help="BME280 address (118, 119, 0x67, 0x77", type=auto_int, choices=(118, 119))
        parser.add_argument("-r", "--bme280_port", help="BME280 I2C port (1, 2)", type=int, choices=(1, 2))
        parser.add_argument("-N", "--bme280_sensor_name", help="BME280 Home Assistant sensor name", type=str)
        parser.add_argument("-I", "--bme280_polling_interval", help="BME280 polling interval", type=int)
        parser.add_argument("-c", "--config", help="config file name (YAML)")
        parser.add_argument("-s", "--secrets", help="secrets file name (YAML) which is merged with and overrides entries in config")

        args = parser.parse_args()

        # determine config/secrets filename and read it
        if args.config:
            config_file = args.config
        else:
            config_file = '.config.yaml'
        config = read_yaml(config_file)
        if args.secrets:
            secrets_file = args.secrets
        else:
            secrets_file = '.secrets.yaml'
        config = read_yaml(config_file)
        secrets = read_yaml(secrets_file)

        # determine logging level from command, if supplied, otherwise config
        if args.loglevel:
            loglevel = args.loglevel.upper()
        elif 'logging' in config and 'level' in config['logging']:
            loglevel = config['logging']['level']
        else:
            loglevel = "WARN"
        if not loglevel in loglevels:
            print(f"logging level({loglevel}) must be one of ({lognames})")
            sys.exit()
        self.logginglevelname = loglevel    
        self.logginglevel = loglevels[loglevel]

        # get MQTT parameters
        self.mqtt = {}
        self.mqtt['broker'] = configOrCmdParm(args.mqtt_broker, config, secrets,['mqtt','broker'], default="localhost")
        print(config)
        print(secrets)
        print(deep_merge_dicts(config, secrets))
        print(self.mqtt['broker'])
        self.mqtt['port'] = configOrCmdParm(args.mqtt_port, config, secrets,['mqtt','portxr'], default=1883)
        self.mqtt['username'] = configOrCmdParm(args.mqtt_username, config, secrets,['mqtt','username'])
        self.mqtt['password'] = configOrCmdParm(args.mqtt_password, config, secrets,['mqtt','password'])
        self.mqtt['polling_interval'] = configOrCmdParm(args.mqtt_password, config, secrets,['mqtt','polling_interval'], default=1)

        # get BME280 parameters
        self.bme280 = {}
        self.bme280['port'] = configOrCmdParm(args.bme280_port, config, secrets,['bme280','port'], default=1)
        self.bme280['address'] = configOrCmdParm(args.bme280_address, config, secrets,['bme280','address'], default=0x76)
        self.bme280['sensor_name'] = configOrCmdParm(args.bme280_address, config, secrets,['bme280','sensor_name'])
        self.bme280['polling_interval'] = configOrCmdParm(args.bme280_address, config, secrets,['bme280','polling_interval'], default=60)

        # get web parameters
        self.web = {}
        self.web['port'] = configOrCmdParm(args.web_port, config, secrets,['web','port'], default=8088)
        self.web['address'] = configOrCmdParm(args.web_address, config, secrets,['web','address'], default='0.0.0.0')

