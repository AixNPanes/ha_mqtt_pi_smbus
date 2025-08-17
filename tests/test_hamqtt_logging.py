# tests/test_hamqtt_logging.py
import json
import logging
from json.decoder import JSONDecodeError
from unittest import TestCase
from unittest.mock import patch, mock_open

from ha_mqtt_pi_smbus.hamqtt_logging import loggerConfig

from .mock_data import MOCK_CPUINFO_DATA, MOCK_OSRELEASE_DATA, MOCK_LOGGING_CONFIG_DATA


class MockOpen:
    builtin_open = open

    def open(self, *args, **kwargs):
        if args[0] == "logging.config":
            return mock.mock_open(read_data=MOCK_CPUINFO_DATA)(*args, **kwargs)
        if args[0] == "/etc/os-release":
            return mock.mock_open(read_data=MOCK_OSRELEASE_DATA)(*args, **kwargs)
        return self.builtin_open(*args, **kwargs)


class MockOpenNF:
    builtin_open = open

    def open(self, *args, **kwargs):
        raise FileNotFoundError()


class MockLogging:
    builtin_open = open

    def dictConfig(self, *args, **kwargs):
        raise FileNotFoundError()


class TestLogging(TestCase):
    @patch("ha_mqtt_pi_smbus.hamqtt_logging.readfile", side_effect=FileNotFoundError)
    def test_file_not_found(self, mock_readfile):
        loggerConfig()
        mock_readfile.assert_called_once_with("logging.config")

    @patch(
        "ha_mqtt_pi_smbus.hamqtt_logging.readfile",
        return_value="""{
                "version": 1
            }""",
    )
    def test_no_disable_existing_loggers(selfi, mockopen):
        loggerConfig()
        mockopen.assert_called_once_with("logging.config")

    @patch("ha_mqtt_pi_smbus.hamqtt_logging.readfile", return_value="bad json content")
    @patch("ha_mqtt_pi_smbus.hamqtt_logging.json.load", side_effect=JSONDecodeError)
    def test_loggerconfig(self, mock_json_load, mock_readfile):
        logger_config = loggerConfig()

        # Assert open called
        mock_readfile.assert_called_once_with("logging.config")
        mock_json_load.assert_not_called()
        self.assertEqual(logger_config["version"], 1)

    @patch("ha_mqtt_pi_smbus.hamqtt_logging.readfile", return_value="anything")
    @patch("ha_mqtt_pi_smbus.hamqtt_logging.json.load", side_effect=TypeError)
    def test_loggerconfig_generic_exception(self, mock_json_load, mock_readfile):
        logger_config = loggerConfig()

        mock_readfile.assert_called_once_with("logging.config")
        mock_json_load.assert_not_called()
        self.assertEqual(logger_config["version"], 1)

    @patch(
        "ha_mqtt_pi_smbus.hamqtt_logging.readfile",
        return_value=json.dumps(MOCK_LOGGING_CONFIG_DATA),
    )
    def test_loggerconfig_disable_existing_loggers(self, mock_readfile):
        logger_config = loggerConfig()

        mock_readfile.assert_called_once_with("logging.config")
        self.assertEqual(logger_config["version"], 1)
        self.assertIn("loggers", logger_config)
        self.assertEqual(logger_config["disable_existing_loggers"], False)
