# tests/test_bme280_parsing.py
import logging
import sys
from unittest import TestCase
from unittest.mock import patch, mock_open
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

class TestParser(TestCase):
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
