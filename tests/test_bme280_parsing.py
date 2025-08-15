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

from .mock_data import (
    MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT,
    MOCK_IFCONFIG_WLAN0_DATA,
    MOCK_IFCONFIG_ETH0_DATA,
    MOCK_CPUINFO_DATA,
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
bme280:
    address: 0x76
    bus: 1
    sensor_name: test
    polling_interval: 1
"""

def mock_open_side_effect(file_name, *args, **kwargs):
    mock_file1 = mock_open(read_data=CONFIG_DATA)
    if file_name == ".config.yaml":
        return mock_file1()  # Call the mock_open instance to get the file handle
    else:
        # Handle cases for other files or raise an error if unexpected
        raise FileNotFoundError(f"File not found: {file_name}")

class TestParser(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('ha_mqtt_pi_smbus.parsing.readfile', return_value=CONFIG_DATA)
    @patch('sys.argv', ['me', '-c', '.config.yaml'])
    def test_bmeparser(self, mock_read):
        from example.pi_bme280.parsing import BME280Parser
        from ha_mqtt_pi_smbus.environ import readfile
        parser = BME280Parser()
        parser.parse_args()
        self.assertEqual(mock_read.call_count, 2)
        self.assertEqual(parser.title, 'title')
        self.assertEqual(parser.subtitle, '')
        self.assertEqual(parser.bme280.address, 118)
        self.assertEqual(parser.bme280.bus, 1)
        self.assertEqual(parser.bme280.sensor_name, 'test')
        self.assertEqual(parser.bme280.polling_interval, 1)
