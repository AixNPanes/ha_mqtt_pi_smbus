# tests/test_parsing.py
import logging
# import sys
from pathlib import Path

# import time
from unittest import TestCase
from unittest.mock import patch, mock_open
import yaml

from ha_mqtt_pi_smbus.parsing import (
    BasicParser,
    WebParser,
    Parser,
)
from ha_mqtt_pi_smbus.util import (
    deep_merge_dicts,
    read_yaml,
    auto_int,
    ipaddress,
)
from .mock_data import MOCK_CONFIG_DATA

CONFIG_DATA = '''---
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
'''
SECRETS_DATA = '''---
title: Title
web:
    address: 5.6.7.8
'''
TOML_DATA = b'version = \'v0.1.2\''


#def mock_open_side_effect(self, file_name, *args, **kwargs):
#    mock_file1 = mock_open(read_data=self.CONFIG_DATA)
#    mock_file2 = mock_open(read_data=self.SECRETS_DATA)
#    mock_file3 = mock_open(read_data=self.TOML_DATA)
#    # Call the mock_open instance to get the file handle
#    if Path(file_name).name == '.config.yaml':
#        return mock_file1()
#    elif Path(file_name).name == 'secrets.yaml':
#        return mock_file2()
#    elif Path(file_name).name == 'pyproject.toml':
#        return mock_file3()
#    else:
#        raise FileNotFoundError(f'File not found: {file_name}')


class TestParser(TestCase):
    @patch('sys.argv', ['me', '--version'])
    @patch('sys.exit')
    @patch('ha_mqtt_pi_smbus.environ.get_pyproject_version', return_value='v0.1.2')
    @patch(
        'ha_mqtt_pi_smbus.util.read_yaml',
        return_value={'title': 'Title', 'subtitle': ''},
    )
    def test_parser_version(self, mock_read_yaml, mock_pyproject_version, mock_exit):
        parser = Parser()
        parser.parse_args()
        mock_exit.assert_called_once()

    @patch('sys.argv', ['me'])
    @patch('ha_mqtt_pi_smbus.environ.get_pyproject_version', return_value='v0.1.2')
    def test_parser_no_args(self, mock_pyproject_version):
        parser = Parser()
        parser.parse_args()
        self.assertEqual(parser._config_dict['mqtt'], {})
        self.assertEqual(parser._config_dict['web'], {})
        self.assertEqual(parser._config_dict['config'], '.config.yaml')
        self.assertNotIn('secrets', parser._config_dict)
        self.assertNotIn('title', parser._config_dict)
        self.assertNotIn('subtitle', parser._config_dict)
        self.assertNotIn('version', parser._config_dict)

    @patch('sys.argv', ['me', '-c', '.config.yaml', '-s', '.secrets.yaml', '-t', 'title'])
    @patch('ha_mqtt_pi_smbus.environ.get_pyproject_version', return_value='v0.1.2')
    @patch(
        'ha_mqtt_pi_smbus.util.read_yaml',
        return_value={'title': 'Title', 'subtitle': ''},
    )
    def test_parser_abbrev_args(self, mock_read_yaml, mock_pyproject_version):
        parser = Parser()
        parser.parse_args()
        self.assertEqual(parser._config_dict['config'], '.config.yaml')
        self.assertEqual(parser._config_dict['secrets'], '.secrets.yaml')
        self.assertEqual(parser._config_dict['title'], 'title')

    @patch('sys.argv', ['me', '--config', '.config.yaml', '--secrets', '.secrets.yaml', '--title', 'title', '--subtitle', 'subtitle'])
    @patch('ha_mqtt_pi_smbus.environ.get_pyproject_version', return_value='v0.1.2')
    @patch(
        'ha_mqtt_pi_smbus.util.read_yaml',
        return_value={'title': 'Title', 'subtitle': ''},
    )
    def test_parser_args(self, mock_read_yaml, mock_pyproject_version):
        parser = Parser()
        parser.parse_args()
        self.assertEqual(parser._config_dict['config'], '.config.yaml')
        self.assertEqual(parser._config_dict['secrets'], '.secrets.yaml')
        self.assertEqual(parser._config_dict['title'], 'title')
        self.assertEqual(parser._config_dict['subtitle'], 'subtitle')

    @patch('sys.argv', ['me', '-w', '1.2.3.4', '-o', '5678'])
    @patch('ha_mqtt_pi_smbus.environ.get_pyproject_version', return_value='v0.1.2')
    @patch(
        'ha_mqtt_pi_smbus.util.read_yaml',
        return_value={'title': 'Title', 'subtitle': ''},
    )
    def test_parser_web_abbrev_args(self, mock_read_yaml, mock_pyproject_version):
        parser = Parser()
        parser.parse_args()
        self.assertEqual(parser._config_dict['web']['address'], b'\x01\x02\x03\x04')
        self.assertEqual(parser._config_dict['web']['port'], 5678)

    @patch('sys.argv', ['me', '--web_address', '1.2.3.4', '--web_port', '5678'])
    @patch('ha_mqtt_pi_smbus.environ.get_pyproject_version', return_value='v0.1.2')
    @patch(
        'ha_mqtt_pi_smbus.util.read_yaml',
        return_value={'title': 'Title', 'subtitle': ''},
    )
    def test_parser_web_args(self, mock_read_yaml, mock_pyproject_version):
        parser = Parser()
        parser.parse_args()
        self.assertEqual(parser._config_dict['web']['address'], b'\x01\x02\x03\x04')
        self.assertEqual(parser._config_dict['web']['port'], 5678)

    @patch('sys.argv', ['me', '-b', 'broker', '-n', '1234', '-u', 'username', '-p', 'password', '-i', '117','-q','1'])
    @patch('ha_mqtt_pi_smbus.environ.get_pyproject_version', return_value='v0.1.2')
    @patch(
        'ha_mqtt_pi_smbus.util.read_yaml',
        return_value={'title': 'Title', 'subtitle': ''},
    )
    def test_parser_mqtt_abbrev_args(self, mock_read_yaml, mock_pyproject_version):
        parser = Parser()
        parser.parse_args()
        self.assertEqual(parser._config_dict['mqtt']['broker'], 'broker')
        self.assertEqual(parser._config_dict['mqtt']['port'], 1234)
        self.assertEqual(parser._config_dict['mqtt']['username'], 'username')
        self.assertEqual(parser._config_dict['mqtt']['password'], 'password')
        self.assertEqual(parser._config_dict['mqtt']['polling_interval'], 117)
        self.assertEqual(parser._config_dict['mqtt']['qos'], 1)

    @patch('sys.argv', ['me', '--mqtt_broker', 'broker', '--mqtt_port', '1234', '--mqtt_username', 'username', '--mqtt_password', 'password', '--mqtt_polling_interval', '117','--mqtt_qos','1', '--mqtt_disable_retain', '--mqtt_auto_discover','--mqtt_expire_after','117','--mqtt_status_topic','homeassistant/status'])
    @patch('ha_mqtt_pi_smbus.environ.get_pyproject_version', return_value='v0.1.2')
    @patch(
        'ha_mqtt_pi_smbus.util.read_yaml',
        return_value={'title': 'Title', 'subtitle': ''},
    )
    def test_parser_mqtt_abbrev_args(self, mock_read_yaml, mock_pyproject_version):
        parser = Parser()
        parser.parse_args()
        self.assertEqual(parser._config_dict['mqtt']['broker'], 'broker')
        self.assertEqual(parser._config_dict['mqtt']['port'], 1234)
        self.assertEqual(parser._config_dict['mqtt']['username'], 'username')
        self.assertEqual(parser._config_dict['mqtt']['password'], 'password')
        self.assertEqual(parser._config_dict['mqtt']['polling_interval'], 117)
        self.assertEqual(parser._config_dict['mqtt']['qos'], 1)
