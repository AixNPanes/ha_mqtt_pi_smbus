# tests/test_confi.py
import logging

import pytest
from unittest import TestCase
from unittest.mock import patch

from ha_mqtt_pi_smbus.config import (
    BasicConfig,
    WebConfig,
    MqttConfig,
    Config,
    getConfig,
)
from ha_mqtt_pi_smbus.parsing import Parser
from .mock_data import MOCK_CONFIG_DATA

CONFIG_JSON = {
    'config': 'config',
    'secrets': 'secrets',
    'title': 'title',
    'subtitle': 'subtitle',
    'web': {
        'address': '1.2.3.4',
        'port': 1234,
    },
    'mqtt': {
        'broker': '5.6.7.8',
        'port': 5678,
        'username': 'me',
        'password': 'mine',
        'polling_interval': 1,
        'qos': 1,
        'disable_retain': False,
        'auto_discover': True,
        'expire_after': 99,
        'status_topic': 'help/me',
    }
}


class TestConfig(TestCase):
    def test_config(self):
        config = Config(CONFIG_JSON)
        self.assertEqual(config.config, 'config')
        self.assertEqual(config.secrets, 'secrets')
        self.assertEqual(config.title, 'title')
        self.assertEqual(config.subtitle, 'subtitle')
        self.assertEqual(config.web.address, '1.2.3.4')
        self.assertEqual(config.web.port, 1234)
        self.assertEqual(config.mqtt.broker, '5.6.7.8')
        self.assertEqual(config.mqtt.port, 5678)
        self.assertEqual(config.mqtt.username, 'me')
        self.assertEqual(config.mqtt.password, 'mine')
        self.assertEqual(config.mqtt.polling_interval, 1)
        self.assertEqual(config.mqtt.qos, 1)
        self.assertEqual(config.mqtt.disable_retain, False)
        self.assertEqual(config.mqtt.auto_discover, True)
        self.assertEqual(config.mqtt.expire_after, 99)
        self.assertEqual(config.mqtt.status_topic, 'help/me')

    def test_sanitize(self):
        config = Config(CONFIG_JSON)
        sanitized = config.sanitize()
        self.assertEqual(sanitized.config, 'config')
        self.assertEqual(sanitized.secrets, 'secrets')
        self.assertEqual(sanitized.title, 'title')
        self.assertEqual(sanitized.subtitle, 'subtitle')
        self.assertEqual(sanitized.web.address, '1.2.3.4')
        self.assertEqual(sanitized.web.port, 1234)
        self.assertEqual(sanitized.mqtt.broker, 'broker')
        self.assertEqual(sanitized.mqtt.port, 'port')
        self.assertEqual(sanitized.mqtt.username, 'username')
        self.assertEqual(sanitized.mqtt.password, 'password')
        self.assertEqual(sanitized.mqtt.polling_interval, 1)
        self.assertEqual(sanitized.mqtt.qos, 1)
        self.assertEqual(sanitized.mqtt.disable_retain, False)
        self.assertEqual(sanitized.mqtt.auto_discover, True)
        self.assertEqual(sanitized.mqtt.expire_after, 99)
        self.assertEqual(sanitized.mqtt.status_topic, 'help/me')

    @patch("sys.argv", ["me", "--mqtt_broker", "broker", "--mqtt_port", "1234", "--mqtt_username", "username", "--mqtt_password", "password", "--mqtt_polling_interval", "117","--mqtt_qos","1", "--mqtt_disable_retain", "--mqtt_auto_discover","--mqtt_expire_after","117","--mqtt_status_topic","homeassistant/status"])
    @patch("ha_mqtt_pi_smbus.environ.get_pyproject_version", return_value="v0.1.2")
    @patch(
        "ha_mqtt_pi_smbus.util.read_yaml",
        return_value={"title": "Title", "subtitle": ""},
    )
    def test_parser_config_no_file(self, mock_read_yaml, mock_pyproject_version):
        parser = Parser()
        parser.parse_args()
        config = Config(parser._config_dict)
        self.assertEqual(config.mqtt.broker, 'broker')
        self.assertEqual(config.mqtt.port, 1234)
        self.assertEqual(config.mqtt.username, 'username')
        self.assertEqual(config.mqtt.password, 'password')
        self.assertEqual(config.mqtt.polling_interval, 117)
        self.assertEqual(config.mqtt.qos, 1)

    @patch("sys.argv", ["me", "--mqtt_broker", "broker", "--mqtt_port", "1234", "--mqtt_username", "username", "--mqtt_password", "password", "--mqtt_polling_interval", "117","--mqtt_qos","1", "--mqtt_disable_retain", "--mqtt_auto_discover","--mqtt_expire_after","117","--mqtt_status_topic","homeassistant/status"])
    @patch("ha_mqtt_pi_smbus.util.readfile", return_value=MOCK_CONFIG_DATA)
    @patch("ha_mqtt_pi_smbus.environ.get_pyproject_version", return_value="v0.1.2")
    @patch(
        "ha_mqtt_pi_smbus.util.read_yaml",
        return_value={"title": "Title", "subtitle": ""},
    )
    def test_parser_config_config_file(self, mock_read_yaml, mock_pyproject_version, mock_readfile):
        parser = Parser()
        parser.parse_args()
        config = Config(parser._config_dict)
        self.assertEqual(config.mqtt.broker, 'broker')
        self.assertEqual(config.mqtt.port, 1234)
        self.assertEqual(config.mqtt.username, 'username')
        self.assertEqual(config.mqtt.password, 'password')
        self.assertEqual(config.mqtt.polling_interval, 117)
        self.assertEqual(config.mqtt.qos, 1)
        self.assertEqual(config.title, 'Bosch BME280')
        self.assertEqual(config.subtitle, 'Temperature, Pressure, Humidity Sensors')
        self.assertEqual(config.web.address, '0.0.0.0')
        self.assertEqual(config.web.port, 8088)
        self.assertEqual(config.mqtt.disable_retain, False)
        self.assertEqual(config.mqtt.auto_discover, True)
        self.assertEqual(config.mqtt.expire_after, 117)

    @patch("sys.argv", ["me", "--secrets",".secrets.yaml","--mqtt_broker", "broker", "--mqtt_port", "1234", "--mqtt_polling_interval", "117","--mqtt_qos","1", "--mqtt_disable_retain", "--mqtt_auto_discover","--mqtt_expire_after","117","--mqtt_status_topic","homeassistant/status"])
    @patch("ha_mqtt_pi_smbus.util.readfile", side_effect=[MOCK_CONFIG_DATA,
"""---
mqtt:
  username: user
  password: pass
""", '', ''])
    @patch("ha_mqtt_pi_smbus.environ.get_pyproject_version", return_value="v0.1.2")
    @patch(
        "ha_mqtt_pi_smbus.util.read_yaml",
        return_value={"title": "Title", "subtitle": ""},
    )
    def test_parser_config_config_and_secrets_file(self, mock_read_yaml, mock_pyproject_version, mock_readfile):
        parser = Parser()
        parser.parse_args()
        config = Config(parser._config_dict)
        self.assertEqual(mock_readfile.call_count, 4)
        self.assertEqual(config.mqtt.broker, 'broker')
        self.assertEqual(config.mqtt.port, 1234)
        self.assertEqual(config.mqtt.username, 'user')
        self.assertEqual(config.mqtt.password, 'pass')
        self.assertEqual(config.mqtt.polling_interval, 117)
        self.assertEqual(config.mqtt.qos, 1)
        self.assertEqual(config.title, 'Bosch BME280')
        self.assertEqual(config.subtitle, 'Temperature, Pressure, Humidity Sensors')
        self.assertEqual(config.web.address, '0.0.0.0')
        self.assertEqual(config.web.port, 8088)
        self.assertEqual(config.mqtt.disable_retain, False)
        self.assertEqual(config.mqtt.auto_discover, True)
        self.assertEqual(config.mqtt.expire_after, 117)        

    def test_getConfig_none(self):
        self.assertEqual(getConfig(None), {})

    def test_Config_none(self):
        config = Config(None)
        self.assertIsNone(config.config)
        self.assertIsNone(config.secrets)
        self.assertIsNone(config.title)
        self.assertIsNone(config.subtitle)

    def test_Config_clone(self):
        config = Config(CONFIG_JSON)
        clone = config.clone()
        self.assertEqual(clone.config, 'config')
        self.assertEqual(clone.secrets, 'secrets')
        self.assertEqual(clone.title, 'title')
        self.assertEqual(clone.subtitle, 'subtitle')
        self.assertEqual(clone.web.address, '1.2.3.4')
        self.assertEqual(clone.web.port, 1234)
        self.assertEqual(clone.mqtt.broker, '5.6.7.8')
        self.assertEqual(clone.mqtt.port, 5678)
        self.assertEqual(clone.mqtt.username, 'me')
        self.assertEqual(clone.mqtt.password, 'mine')
        self.assertEqual(clone.mqtt.polling_interval, 1)
        self.assertEqual(clone.mqtt.qos, 1)
        self.assertEqual(clone.mqtt.disable_retain, False)
        self.assertEqual(clone.mqtt.auto_discover, True)
        self.assertEqual(clone.mqtt.expire_after, 99)
        self.assertEqual(clone.mqtt.status_topic, 'help/me')