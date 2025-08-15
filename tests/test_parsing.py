# tests/test_parsing.py
import logging
import sys
from pathlib import Path
import time
from unittest import TestCase
from unittest.mock import patch, mock_open
import yaml

from ha_mqtt_pi_smbus.parsing import Parser, deep_merge_dicts, read_yaml, auto_int, ipaddress, configOrCmdParm, BasicParser, WebParser, MQTTParser, Parser

from .mock_data import (
    MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT,
    MOCK_IFCONFIG_WLAN0_DATA,
    MOCK_IFCONFIG_ETH0_DATA,
    #MOCKED_OPEN,
)


CONFIG_DATA="""---
title: title
web:
    address: 1.2.3.4
    port: 1234
mqtt:
    broker: 5.6.7.8
    port: 5678
    username: me
    password: mine
    qos: 1
    disable_retain: False
    auto_discover: True
    expire_after: 99
"""
SECRETS_DATA="""---
title: Title
web:
    address: 5.6.7.8
"""
TOML_DATA=b'version = "v0.1.2"'

def mock_open_side_effect(self, file_name, *args, **kwargs):
    mock_file1 = mock_open(read_data=self.CONFIG_DATA)
    mock_file2 = mock_open(read_data=self.SECRETS_DATA)
    mock_file3 = mock_open(read_data=self.TOML_DATA)
    # Call the mock_open instance to get the file handle
    if Path(file_name).name == ".config.yaml":
        return mock_file1()
    elif Path(file_name).name == "secrets.yaml":
        return mock_file2()
    elif Path(file_name).name == "pyproject.toml":
        return mock_file3()
    else:
       raise FileNotFoundError(f"File not found: {file_name}")

class TestParser(TestCase):
    def test_deep_merge_dicts(self):
        dict1 = {
                "a": "a",
                "b": "b",
                "c": {
                    "d": "d",
                    "e": "e",
                    },
                "f": {
                    "g": "g",
                    "h": "h",
                    "i": {
                        "j": "j",
                        "k": "k"
                        },
                    },
                }
        dict2 = {"f": {"i": {"j": "jj", "l": "ll"}}}
        dict3 = deep_merge_dicts(dict1, dict2)
        dict1["a"] = "1"
        self.assertEqual(len(dict3), 4)
        self.assertEqual(len(dict3["f"]), 3)
        self.assertEqual(len(dict3["f"]["i"]), 3)
        self.assertEqual(dict3["f"]["i"]["j"], 'jj')
        self.assertEqual(dict1["a"], "1")
        self.assertEqual(dict3["a"], "a")
        dict3 = deep_merge_dicts(dict1, {})
        self.assertEqual(len(dict3), len(dict1))
        dict3 = deep_merge_dicts({}, dict2)
        self.assertEqual(dict3, {'f': {'i': {'j': 'jj', 'l': 'll'}}})

    @patch('ha_mqtt_pi_smbus.parsing.readfile', return_value="""---
a:
   b: b
""")
    def test_read_yaml_ok(self, mock_read):
        data = read_yaml(mock_read)
        self.assertEqual(data, {"a": {"b": "b"}})

    @patch('ha_mqtt_pi_smbus.parsing.read_yaml', side_effect=yaml.YAMLError)
    @patch('ha_mqtt_pi_smbus.parsing.readfile', return_value="""
---
a:a
   b: b
   c: c
""")
    def test_read_yaml_bad_yaml(self, mock_read, mock_read_yaml):
        data = read_yaml(mock_read)
        self.assertEqual(data, None)

    @patch('ha_mqtt_pi_smbus.parsing.read_yaml', side_effect=FileNotFoundError)
    def test_read_yaml_file_not_found(self, mock_read_yaml):
        data = read_yaml("bad.file")
        self.assertEqual(data, None)

    def test_auto_int(self):
        self.assertEqual(auto_int("0x0a"), 10)
        self.assertEqual(auto_int("0b1010"), 10)
        self.assertEqual(auto_int("0o12"), 10)
        self.assertEqual(auto_int("10"), 10)

    @patch('ha_mqtt_pi_smbus.parsing.ipaddress', side_effect=OSError)
    def test_ipaddress(self, mock_ipaddress):
        self.assertEqual(ipaddress("127.0.0.1").hex(), "7f000001")
        self.assertEqual(ipaddress("192.168.1.211").hex(), "c0a801d3")
        self.assertEqual(ipaddress("256.168.1.211"), None)

    @patch.object(sys, 'exit')
    def test_configOrCmdParam_arg(self, mock_exit):
        self.assertEqual(configOrCmdParm(1, {}, ()), 1)
        self.assertEqual(configOrCmdParm(1, {'A':{'B':1}}, ['A', 'B'], ), 1)
        self.assertEqual(configOrCmdParm(None,  {'A':{'B': 'Z'}}, ['A', 'B'], ), 'Z')
        self.assertEqual(configOrCmdParm(None, {'A':{'B': 'Z'}}, ['A', 'C'], required=True), None)
        mock_exit.assert_called_once_with()

    @patch('sys.argv', ['me', '-c', '.config.yaml', '-s', 'secrets.yaml'])
    @patch('ha_mqtt_pi_smbus.parsing.read_yaml', return_value={'title': 'Title', 'subtitle': ''})
    def test_basic_parser(self, mock_read_yaml):
        parser = BasicParser()
        parser.parse_args()
        self.assertEqual(parser.title, 'Title')
        self.assertEqual(parser.subtitle, '')

    @patch('sys.argv', ['me'])
    @patch('ha_mqtt_pi_smbus.parsing.read_yaml', return_value={'web': {'address': '1.2.3.4', 'port': 1234}})
    def test_web_parser(self, mock_read_yaml):
        parser = WebParser()
        parser.parse_args()
        self.assertEqual(parser.web.address, '1.2.3.4')
        self.assertEqual(parser.web.port, 1234)

    @patch('sys.argv', ['me'])
    @patch('ha_mqtt_pi_smbus.parsing.read_yaml', return_value={'mqtt': {'broker': '5.6.7.8', 'port': 5678, 'username': 'me', 'password': 'mine', 'qos': 1, 'disable_retain': False, 'retain': True, 'auto_discover': True, 'expire_after': 99}})
    def test_parser(self, mock_read_yaml):
        parser = Parser()
        parser.parse_args()
        self.assertEqual(parser.mqtt.broker, '5.6.7.8')
        self.assertEqual(parser.mqtt.port, 5678)
        self.assertEqual(parser.mqtt.username, 'me')
        self.assertEqual(parser.mqtt.password, 'mine')
        self.assertEqual(parser.mqtt.qos, 1)
        self.assertEqual(parser.mqtt.disable_retain, False)
        self.assertEqual(parser.mqtt.retain, True)
        self.assertEqual(parser.mqtt.auto_discover, True)
        self.assertEqual(parser.mqtt.expire_after, 99)

    @patch('sys.argv', ['me', '--version'])
    @patch('sys.exit')
    @patch('ha_mqtt_pi_smbus.parsing.read_yaml', return_value={'version': True})
    def test_version(self, mock_read_yaml, mock_exit):
        parser = Parser()
        parser.parse_args()
        self.assertTrue(parser.version)
