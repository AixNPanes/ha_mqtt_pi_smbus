# tests/test_bme280_parsing.py
import logging
import sys
from unittest import TestCase
from unittest.mock import patch, mock_open
import yaml

from example.pi_bme280.parsing import Bme280Config, BME280Parser
from ha_mqtt_pi_smbus.config import dict_to_config
from ha_mqtt_pi_smbus.parsing import Config
from .mock_data import (
    MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT,
    MOCK_IFCONFIG_WLAN0_DATA,
    MOCK_IFCONFIG_ETH0_DATA,
    MOCK_CPUINFO_DATA,
    MOCK_CONFIG_DATA,
)


class TestParser(TestCase):
    @patch("sys.argv", ["me", "-c", ".config.yaml"])
    def test_bmeparser(self):
        parser = BME280Parser()
        parser.parse_args()
        self.assertEqual(parser._config_dict['config'], '.config.yaml')

    @patch("ha_mqtt_pi_smbus.util.readfile", return_value=MOCK_CONFIG_DATA)
    @patch("sys.argv", ["me", "-c", ".config.yaml", "-a", "0x77", "-r", "2", "-N", "tph281","-I", "2"])
    def test_bmeparser(self, mock_read):
        parser = BME280Parser()
        parser.parse_args()
        config = dict_to_config(parser._config_dict)
        mock_read.assert_called_once()
        self.assertEqual(mock_read.call_count, 1)
        self.assertEqual(config.config, '.config.yaml')
        self.assertIsNone(config.secrets)
        self.assertEqual(config.title, 'Bosch BME280')
        self.assertEqual(config.subtitle, 'Temperature, Pressure, Humidity Sensors')
        self.assertIsNotNone(config.web)
        self.assertEqual(config.web.address, '0.0.0.0')
        self.assertEqual(config.web.port, 8088)
        self.assertIsNotNone(config.logging)
        self.assertEqual(config.logging.level, 'ERROR')
        self.assertIsNotNone(config.mqtt)
        self.assertEqual(config.mqtt.broker, 'hastings.attlocal.net')
        self.assertEqual(config.mqtt.port, 1883)
        self.assertEqual(config.mqtt.username, 'mqttuser')
        self.assertEqual(config.mqtt.password, 'mqttuser-password')
        self.assertEqual(config.mqtt.polling_interval, 1)
        self.assertEqual(config.mqtt.qos, 0)
        self.assertEqual(config.mqtt.disable_retain, False)
        self.assertEqual(config.mqtt.auto_discover, True)
        self.assertEqual(config.mqtt.expire_after, 119)
        self.assertIsNotNone(config.bme280)
        self.assertEqual(config.bme280.address, 119)
        self.assertEqual(config.bme280.bus, 2)
        self.assertEqual(config.bme280.sensor_name, 'tph281')
        self.assertEqual(config.bme280.polling_interval, 2)
