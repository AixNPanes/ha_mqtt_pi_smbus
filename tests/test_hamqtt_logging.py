# tests/test_hamqtt_loging.py
from argparse import Namespace
from json.decoder import JSONDecodeError
import logging
import pytest
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch, mock_open

from ha_mqtt_pi_smbus.hamqtt_logging import loggerConfig

class MockOpen:
    builtin_open = open

    def open(self, *args, **kwargs):
        if args[0] == "logging.config":
            return mock.mock_open(read_data="""
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
 """)(*args, **kwargs)
        if args[0] == "/etc/os-release":
            return mock.mock_open(read_data="""
                PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
                NAME="Debian GNU/Linux"
                VERSION_ID="12"
                VERSION="12 (bookworm)"
                VERSION_CODENAME=bookworm
                ID=debian
                HOME_URL="https://www.debian.org/"
                SUPPORT_URL="https://www.debian.org/support"
                BUG_REPORT_URL="https://bugs.debian.org/"
            """)(*args, **kwargs)
        return self.builtin_open(*args, **kwargs)

class MockOpenNF:
    builtin_open = open

    def open(self, *args, **kwargs):
        raise FileNotFoundError()

class MockLogging:
    builtin_open = open

    def dictConfig(self, *args, **kwargs):
        raise FileNotFoundError()

class TestLogging(unittest.TestCase):
    def setUp(self):

        parser = Namespace(
            logginglevel='DEBUG',
            title='Test Title',
            subtitle='Test Subtitle'
        )

    def test_file_not_found(self):
        with patch('ha_mqtt_pi_smbus.hamqtt_logging.open', side_effect=FileNotFoundError) as mock_open:
            loggerConfig()
            mock_open.assert_called_once_with("logging.config", "r")

    def test_no_disable_existing_loggers(self):
        m = mock_open(read_data="""{
                "version": 1
            }""")
        with patch('ha_mqtt_pi_smbus.hamqtt_logging.open', m) as mockopen:
            cfg = loggerConfig()
            mockopen.assert_called_once_with("logging.config", "r")

    def test_loggerconfig(self):
        m = mock_open(read_data="bad json content")

        # Patch open and json.load
        with patch('ha_mqtt_pi_smbus.hamqtt_logging.open', m):
            with patch('ha_mqtt_pi_smbus.hamqtt_logging.json.load') as mock_json_load:
                # Make json.load() raise JSONDecodeError with valid args
                mock_json_load.side_effect = JSONDecodeError("Expecting value", "bad json content", 0)
    
                loggerConfig()
    
                # Assert open called
                m.assert_called_once_with('logging.config', 'r')
                mock_json_load.assert_called_once()

    def test_loggerconfig_generic_exception(self):
        m = mock_open(read_data="anything")

        # Patch open to succeed
        with patch('ha_mqtt_pi_smbus.hamqtt_logging.open', m):
            # Patch json.load to raise an *unexpected* exception
            with patch('ha_mqtt_pi_smbus.hamqtt_logging.json.load') as mock_json_load:
                mock_json_load.side_effect = TypeError("Oops!")

                loggerConfig()

                m.assert_called_once_with('logging.config', 'r')
                mock_json_load.assert_called_once()
