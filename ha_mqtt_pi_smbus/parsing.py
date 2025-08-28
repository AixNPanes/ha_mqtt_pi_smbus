from argparse import ArgumentParser
import copy
import logging
import socket
import sys
from typing import Any, Dict
import yaml

from importlib.metadata import version, PackageNotFoundError

from ha_mqtt_pi_smbus.config import BasicConfig, WebConfig, MqttConfig, Config
from ha_mqtt_pi_smbus.environ import get_my_version
from ha_mqtt_pi_smbus.util import ipaddress, deep_merge_dicts, read_yaml


class BasicParser(ArgumentParser):
    '''Parse root level command line parameters and merge with config files

    Parameters
    ----------
    see : ArgumentParser

    '''

    def __init__(self):
        super().__init__(
            description='Raspberry Pi BME280 Home Assistant MQTT client '
            + 'for temperature, pressure and humidity',
            epilog='This  program starts a simple web server which can be '
            + 'used to connect /disconnect the MQTT client and '
            + 'enable/disable device discovery. Without these 2 '
            + 'operations, the device wil not appear in Home Assistant.',
        )
        self.add_argument(
            '-c', '--config', help='config file name (YAML), default(.config.yaml)',default='.config.yaml'
        )
        self.add_argument(
            '-s',
            '--secrets',
            help='secrets file name (YAML) which is merged with '
            + 'and overrides entries in config',
        )
        self.add_argument(
            '-t', '--title', help='the title for the web management interface'
        )
        self.add_argument(
            '--subtitle', help='the subtitle for the web management interface'
        )
        self.add_argument(
            '-v', '--version', action='store_true', help='print the version number'
        )

    def parse_args(self) -> None:
        '''Parse commandline arguments and merge with config files'''
        self.args = super().parse_args()
        
        if self.args.version:
            print(f'\nVersion: {get_my_version()}\n')
            sys.exit()

        # determine title/subtitle from command, if supplied, otherwise config
        dictionary = {}
        if self.args.config:
            dictionary['config'] = self.args.config
        if self.args.secrets:
            dictionary['secrets'] = self.args.secrets
        if self.args.title:
            dictionary['title'] = self.args.title
        if self.args.subtitle:
            dictionary['subtitle'] = self.args.subtitle
        self._config_dict = dictionary


class WebParser(BasicParser):
    '''Parse web command line parameters and merge with config files

    Parameters
    ----------
    None

    '''

    def __init__(self):
        super().__init__()
        self.add_argument(
            '-w',
            '--web_address',
            help='The address the web server listens on, default(0.0.0.0)',
            type=ipaddress,
        )
        self.add_argument(
            '-o',
            '--web_port',
            help='The port the web server listens on, default(8088)',
            type=int,
        )

    def parse_args(self) -> None:
        super().parse_args()

        # get web port/address
        web = {}
        if self.args.web_port:
            web['port'] = self.args.web_port
        if self.args.web_address:
            web['address'] = self.args.web_address
        self._config_dict['web'] = web


class MQTTParser(WebParser):
    '''Parse MQTT command line parameters and merge with config files

    Parameters
    ----------
    None

    '''

    def __init__(self):
        super().__init__()
        self.add_argument('-b', '--mqtt_broker', help='MQTT Broker hostname or address')
        self.add_argument('-n', '--mqtt_port', help='MQTT Broker port number', type=int)
        self.add_argument(
            '-u', '--mqtt_username', '--username', '--user', help='MQTT username'
        )
        self.add_argument('-p', '--mqtt_password', '--password', help='MQTT password')
        self.add_argument(
            '-i',
            '--mqtt_polling_interval',
            help='MQTT polling interval to check sensor data',
            type=int,
        )
        self.add_argument(
            '-q',
            '--mqtt_qos',
            help='MQTT Quality of Service (0, 1, 2). Check HA MQTT '
            + 'documentation for descrition. Default(0)',
            type=int,
            choices=(0, 1, 2),
        )
        self.add_argument(
            '--mqtt_disable_retain',
            help='MQTT retain policy. Check HA MQTT documentation '
            + 'for descrition. Default(true)',
            action='store_false',
        )
        self.add_argument(
            '--mqtt_auto_discover',
            help='perform automatic discovery without web interaction',
            action='store_true',
        )
        self.add_argument(
            '--mqtt_expire_after',
            help='MQTT will mark a device unavailable if not heaard from',
            type=int,
        )
        self.add_argument(
            '--mqtt_status_topic',
            help='MQTT status topic for Last Will and testament, normally homeassistant/status, but configurable from Home Assistan MQTT1',
            type=str,
        )

    def parse_args(self) -> None:
        super().parse_args()

        # get MQTT parameters
        mqtt = {}
        if self.args.mqtt_broker:
            mqtt['broker'] = self.args.mqtt_broker
        if self.args.mqtt_port:
            mqtt['port'] = self.args.mqtt_port
        if self.args.mqtt_username:
            mqtt['username'] = self.args.mqtt_username
        if self.args.mqtt_password:
            mqtt['password'] = self.args.mqtt_password
        if self.args.mqtt_qos:
            mqtt['qos'] = self.args.mqtt_qos
        if self.args.mqtt_polling_interval:
            mqtt['polling_interval'] = self.args.mqtt_polling_interval
        if not self.args.mqtt_disable_retain:
            mqtt['retain'] = not self.args.mqtt_disable_retain
        if self.args.mqtt_auto_discover:
            mqtt['auto_discover'] = self.args.mqtt_auto_discover
        if self.args.mqtt_expire_after:
            mqtt['expire_after'] = self.args.mqtt_expire_after
        if self.args.mqtt_status_topic:
            mqtt['status_topic'] = self.args.mqtt_status_topic
        self._config_dict['mqtt'] = mqtt


class Parser(MQTTParser):
    '''Parse all command line parameters and merge with config files

    Parameters
    ----------
    None

    '''

    def __init__(self):
        super().__init__()

    def parse_args(self):
        super().parse_args()
