# tests/test_environ.py
import builtins
import logging
import subprocess
import sys
import types
import unittest
from unittest import mock
from unittest.mock import patch, mock_open

import ha_mqtt_pi_smbus
from ha_mqtt_pi_smbus.environ import (
    readfile,
    get_command_data,
    _get_pyproject_version,
    _get_setuptools_version,
    _get_metadata_version,
    _get_package_version,
    getTemperature,
    getMacAddress,
    getMacAddressByInterface,
    getObjectId,
    getCpuInfo,
    getOSInfo,
    getUptime,
    getLastRestart,
    get_version,
)


class TestDevice(unittest.TestCase):
    def test_readfile(self):
        null = readfile('/dev/null')
        self.assertEqual(len(null), 0)
        mock_file = mock.mock_open(read_data='mock_data')
        with patch('builtins.open', mock_file):
            data = readfile('mock_data')
            self.assertEqual(data, 'mock_data')
        mock_file.reset_mock()

    def test_getcmd_success(self):
        self.assertEqual(get_command_data(['echo','Hello! World!']), 'Hello! World!\n')

    @patch('subprocess.check_output')
    def test_getcmd_fail(self, mock_check_output):
        mock_check_output.side_effect = subprocess.CalledProcessError(
            returncode=1,  # Non-zero exit status
            cmd="some_command",
            stderr="Error output from command")
        result = get_command_data(['echo', 'Hello! World!'])
        self.assertIsNone(result)

    @patch('ha_mqtt_pi_smbus.environ.readfile', return_value='version = "v0.1.2"')
    def test_get_pyproject_version(self, mock_read):    
        content = _get_pyproject_version()
        self.assertEqual(content, 'v0.1.2')

    @patch('ha_mqtt_pi_smbus.environ.get_command_data', return_value='v0.1.2')
    def test_get_setuptools_version(self, mock_data):    
        content = _get_setuptools_version()
        self.assertEqual(content, 'v0.1.2')

    @patch('importlib.metadata.version', return_value='v0.1.2')
    def test_get_metadata_version(self, mock_version):    
        content = _get_metadata_version()
        self.assertEqual(content, 'v0.1.2')

    @patch('ha_mqtt_pi_smbus.__version__', 'v0.1.2')
    def test_get_package_version(self):    
        self.assertEqual(_get_package_version(), 'v0.1.2')

    @patch('ha_mqtt_pi_smbus.environ.readfile', return_value='12.345')
    def test_temperature(self, mock_read):
        content = getTemperature()
        self.assertEqual(content, 0.012345)

    @patch('ha_mqtt_pi_smbus.environ.get_command_data', return_value="""
            eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:18  txqueuelen 1000  (Ethernet)
        """)
    def test_mac_address_eth_success(self, mock_getcmd):
        mac = getMacAddressByInterface("eth0")
        self.assertEqual(mac, "b8:27:eb:94:a7:18")

    @patch('ha_mqtt_pi_smbus.environ.get_command_data', return_value="""
            wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:19  txqueuelen 1000  (Ethernet)
        """)
    def test_mac_address_wlan_success(self, mock_getcmd):
        mac = getMacAddressByInterface("wlan0")
        self.assertEqual(mac, "b8:27:eb:94:a7:19")

    @patch('ha_mqtt_pi_smbus.environ.get_command_data', side_effect=[None,
            """wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:19  txqueuelen 1000  (Ethernet)
        """])
    def test_mac_address_fake_except(self, mock_getcmd):
        mac = getMacAddressByInterface("fake0")
        self.assertIsNone(mac)

    @patch('ha_mqtt_pi_smbus.environ.get_command_data', side_effect=[None,
            """wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:19  txqueuelen 1000  (Ethernet)
        """])
    def test_mac_address_no_parm(self, mock_getcmd):
        mac = getMacAddress()
        self.assertEqual(mac, 'b8:27:eb:94:a7:19')

    @patch('ha_mqtt_pi_smbus.environ.get_command_data', return_value="""
            eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:18  txqueuelen 1000  (Ethernet)
        """)
    def test_objectid(self, mock_getcmd):
        id = getObjectId()
        self.assertEqual(id, "b827eb94a718")

    @patch('ha_mqtt_pi_smbus.environ.readfile', return_value="""processor	: 0
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

processor	: 2
BogoMIPS	: 38.40
Features	: fp asimd evtstrm crc32 cpuid
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd03
CPU revision	: 4

processor	: 3
BogoMIPS	: 38.40
Features	: fp asimd evtstrm crc32 cpuid
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd03
CPU revision	: 4

Revision	: a22082
Serial		: 000000009ec1f24d
Model		: Raspberry Pi 3 Model B Rev 1.2""")
    def test_cpuinfo(self, mock_read):
        cpu = getCpuInfo()
        self.assertIn("cpu", cpu)
        self.assertEqual(cpu["cpu"]["Revision"], "a22082")

    @patch('ha_mqtt_pi_smbus.environ.readfile', return_value='''PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
NAME="Debian GNU/Linux"
VERSION_ID="12"
VERSION="12 (bookworm)"
VERSION_CODENAME=bookworm
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"''')
    def test_osinfo(self, mock_read):
        osinf = getOSInfo()
        self.assertEqual(osinf["ID"], "debian")

    @patch('ha_mqtt_pi_smbus.environ.get_command_data', return_value="up 2 days, 7 hours, 0 minutes")
    def test_uptime(self, mock_getcmd):
        uptime = getUptime()
        self.assertEqual(uptime, "up 2 days, 7 hours, 0 minutes")

    @patch('ha_mqtt_pi_smbus.environ.get_command_data', return_value="2020-01-01 01:02:03")
    def test_last_restart(self, mock_getcmd):
        uptime = getLastRestart()
        self.assertEqual(uptime, "2020-01-01 01:02:03")

    @patch('ha_mqtt_pi_smbus.environ._get_pyproject_version', return_value=None)
    def test_get_pyproject_none(self, mock_get):
        version = _get_pyproject_version()
        self.assertIsNone(version)

    @patch('ha_mqtt_pi_smbus.environ._get_pyproject_version', side_effect=
        subprocess.CalledProcessError(
            returncode=1,  # Non-zero exit status
            cmd="some_command",
            stderr="Error output from command")
          )
    def test_get_metadata_error(self, mock_get):
        version = _get_metadata_version()
        self.assertIsNone(version)

    @patch('ha_mqtt_pi_smbus.environ._get_metadata_version', side_effect=
        [subprocess.CalledProcessError(
            returncode=1,  # Non-zero exit status
            cmd="some_command",
            stderr="Error output from command")] * 2
          )
    def test_get_metadata_error(self, mock_get):
        version = _get_metadata_version()
        self.assertIsNone(version)

    def test_get_package_error(self):
        original_import = builtins.__import__

        def side_effect(name, globals=None, locals=None, fromlist=(), level=0):
            if fromlist == ('__version__',):
                raise ImportError
            return original_import(name, globals, locals, fromlist, level)

        with unittest.mock.patch('builtins.__import__', side_effect=side_effect):
            version = _get_package_version()
            self.assertIsNone(version)
            version = get_version()
            self.assertEqual(version, '0.0.0-dev')

    def test_get_version(self):
        with patch('ha_mqtt_pi_smbus.environ._get_pyproject_version', return_value='v0.1.3'):
            self.assertEqual(get_version(), 'v0.1.3')
        with patch('ha_mqtt_pi_smbus.environ._get_setuptools_version', return_value='v0.1.4'):
            self.assertEqual(get_version(), 'v0.1.4')
        with patch('ha_mqtt_pi_smbus.environ._get_metadata_version', return_value='v0.1.5'):
            self.assertEqual(get_version(), 'v0.1.5')
        with patch('ha_mqtt_pi_smbus.environ._get_package_version', return_value='v0.1.6'):
            self.assertEqual(get_version(), 'v0.1.6')
