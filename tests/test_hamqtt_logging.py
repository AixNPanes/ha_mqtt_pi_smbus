# tests/test_hamqtt_logging.py
from json.decoder import JSONDecodeError
from unittest import TestCase
from unittest.mock import patch, mock_open

from ha_mqtt_pi_smbus.hamqtt_logging import loggerConfig


class MockOpen:
    builtin_open = open

    def open(self, *args, **kwargs):
        if args[0] == "logging.config":
            return mock.mock_open(
                read_data="""
processor	: 00
BogoMIPS	: 38.40
Features	: fp asimd evtstrm crc32 cpuid
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd03
CPU revision	: 4

processor	: 1
BogoMIPS	: 38.40
Features	: fp asimd evtstrm crc32 cpuid
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd03
CPU revision	: 4

Revision	: a22082
Serial		: 000000009ec1f24d
Model		: Raspberry Pi 3 Model B Rev 1.2
 """
            )(*args, **kwargs)
        if args[0] == "/etc/os-release":
            return mock.mock_open(
                read_data="""
                PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
                NAME="Debian GNU/Linux"
                VERSION_ID="12"
                VERSION="12 (bookworm)"
                VERSION_CODENAME=bookworm
                ID=debian
                HOME_URL="https://www.debian.org/"
                SUPPORT_URL="https://www.debian.org/support"
                BUG_REPORT_URL="https://bugs.debian.org/"
            """
            )(*args, **kwargs)
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
    @patch("ha_mqtt_pi_smbus.hamqtt_logging.open", side_effect=FileNotFoundError)
    def test_file_not_found(self, mock_logging_open):
        loggerConfig()
        mock_logging_open.assert_called_once_with("logging.config", "r")

    @patch("ha_mqtt_pi_smbus.hamqtt_logging.open", return_value="""{
                "version": 1
            }""")
    def test_no_disable_existing_loggers(selfi, mockopen):
            loggerConfig()
            mockopen.assert_called_once_with("logging.config", "r")

    @patch("ha_mqtt_pi_smbus.hamqtt_logging.open", return_value="bad json content")
    @patch("ha_mqtt_pi_smbus.hamqtt_logging.json.load", side_effect = JSONDecodeError("Expecting value", "bad json content", 0))

    def test_loggerconfig(self, mock_json_load, mock_logging_open):
        loggerConfig()
    
        # Assert open called
        mock_logging_open.assert_called_once_with("logging.config", "r")
        mock_json_load.assert_not_called()

    @patch("ha_mqtt_pi_smbus.hamqtt_logging.open", return_value="anything")
    @patch("ha_mqtt_pi_smbus.hamqtt_logging.json.load", side_effect=TypeError("Oops!"))
    def test_loggerconfig_generic_exception(self, mock_json_load, mock_logging_open):
        loggerConfig()

        mock_logging_open.assert_called_once_with("logging.config", "r")
        mock_json_load.assert_not_called()
