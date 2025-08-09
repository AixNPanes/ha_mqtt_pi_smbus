# tests/test_mqtt_client.py
from argparse import Namespace
import io
import logging
import sys
import pytest
import time
import unittest
from unittest import mock
from unittest.mock import patch, mock_open, MagicMock
import yaml

from ha_mqtt_pi_smbus.parsing import Parser, deep_merge_dicts, read_yaml, auto_int, ipaddress, configOrCmdParm, BasicParser, WebParser, MQTTParser, Parser

from .mock_data import (
    MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT,
    MOCK_IFCONFIG_WLAN0_DATA,
    MOCK_IFCONFIG_ETH0_DATA,
    MOCKED_OPEN,
)



class TestParser(unittest.TestCase):
    def setUp(self):
        self.parser = Namespace(
            logginglevel="DEBUG", title="Test Title", subtitle="Test Subtitle"
        )
        self.mocked_open = MOCKED_OPEN
        self.mocked_open.start()

    def tearDown(self):
        self.mocked_open.stop()

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

    def test_read_yaml_ok(self):
        mock_data = """
---
a:
   b: b
"""
        # Create a mock_open object with the desired read_data
        mock_file = mock.mock_open(read_data=mock_data)
        with mock.patch('builtins.open', mock_file):
            data = read_yaml(mock_file)
            self.assertEqual(data, {"a": {"b": "b"}})

    def test_read_yaml_bad_yaml(self):
        mock_data = """
---
a:s
   b: b
"""
        # Create a mock_open object with the desired read_data
        mock_file = mock.mock_open(read_data=mock_data)
        with patch('ha_mqtt_pi_smbus.parsing.read_yaml', side_effect=yaml.YAMLError):
            with mock.patch('builtins.open', mock_file):
                data = read_yaml(mock_file)
                self.assertEqual(data, None)

    def test_read_yaml_file_not_found(self):
        with patch('ha_mqtt_pi_smbus.parsing.read_yaml', side_effect=FileNotFoundError):
            data = read_yaml("bad.file")
            self.assertEqual(data, None)

    def test_auto_int(self):
        self.assertEqual(auto_int("0x0a"), 10)
        self.assertEqual(auto_int("0b1010"), 10)
        self.assertEqual(auto_int("0o12"), 10)
        self.assertEqual(auto_int("10"), 10)

    def test_ipaddress(self):
        self.assertEqual(ipaddress("127.0.0.1").hex(), "7f000001")
        self.assertEqual(ipaddress("192.168.1.211").hex(), "c0a801d3")
        with patch('ha_mqtt_pi_smbus.parsing.ipaddress', side_effect=OSError):
            self.assertEqual(ipaddress("256.168.1.211"), None)

    def test_configOrCmdParam_arg(self):
        self.assertEqual(configOrCmdParm(1, {}, ()), 1)
        self.assertEqual(configOrCmdParm(1, {'A':{'B':1}}, ['A', 'B'], ), 1)
        self.assertEqual(configOrCmdParm(None,  {'A':{'B': 'Z'}}, ['A', 'B'], ), 'Z')
        with mock.patch.object(sys, 'exit') as mock_exit:
            self.assertEqual(configOrCmdParm(None, {'A':{'B': 'Z'}}, ['A', 'C'], required=True), None)
            mock_exit.assert_called_once_with()


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

    def mock_open_side_effect(self, file_name, *args, **kwargs):
        mock_file1 = mock_open(read_data=self.CONFIG_DATA)
        mock_file2 = mock_open(read_data=self.SECRETS_DATA)
        if file_name == ".config.yaml":
            return mock_file1()  # Call the mock_open instance to get the file handle
        elif file_name == "secrets.yaml":
            logging.getLogger(__name__).error(yaml.safe_load(mock_file2()))
            return mock_file2()
        else:
            # Handle cases for other files or raise an error if unexpected
            raise FileNotFoundError(f"File not found: {file_name}")

    @patch('builtins.open')
    def test_basic_parser(self, mock_builtins_open):
        mocker = MagicMock()
        mock_builtins_open.side_effect=self.mock_open_side_effect
        with patch('sys.argv', ['me', '-c', '.config.yaml', '-s', 'secrets.yaml']):
            parser = BasicParser()
            parser.parse_args()
            self.assertEqual(parser.title, 'Title')
            self.assertEqual(parser.subtitle, '')

    @patch('builtins.open')
    def test_web_parser(self, mock_builtins_open):
        mocker = MagicMock()
        mock_builtins_open.side_effect=self.mock_open_side_effect
        with patch('sys.argv', ['me']):
            parser = WebParser()
            parser.parse_args()
            self.assertEqual(parser.web.address, '1.2.3.4')
            self.assertEqual(parser.web.port, 1234)

    @patch('builtins.open')
    def test_parser(self, mock_builtins_open):
        mocker = MagicMock()
        mock_builtins_open.side_effect=self.mock_open_side_effect
        with patch('sys.argv', ['me']):
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

    @patch('sys.exit')
    @patch('importlib.metadata.version', side_effect=Exception("error"))
    @patch('builtins.open')
    def test_version(self, mock_builtins_open, mock_version, mock_exit):
        mocker = MagicMock()
        mock_builtins_open.side_effect=self.mock_open_side_effect
        with patch('sys.argv', ['me', '--version']):
            parser = Parser()
            parser.parse_args()
            self.assertTrue(parser.version)
