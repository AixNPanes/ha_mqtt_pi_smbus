# tests/test_environ.py
import builtins
import importlib
import logging
import subprocess
import sys
import types
import unittest
from unittest import mock
from unittest.mock import patch, mock_open

import ha_mqtt_pi_smbus
import ha_mqtt_pi_smbus.environ as ha_env

from .mock_data import MOCK_CPUINFO_DATA, MOCK_OSRELEASE_DATA


class TestDevice(unittest.TestCase):
    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=43812)
    def test_get_temperature(self, mock_readfile):
        temperature = ha_env.get_temperature()
        self.assertEqual(temperature, 43.812)

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    def test_get_cpu_info(self, mock_readfile):
        cpu_info = ha_env.get_cpu_info()
        self.assertEqual(cpu_info['cpu']['Model'], 'Raspberry Pi 3 Model B Rev 1.2')

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_OSRELEASE_DATA)
    def test_get_osinfo(self, mock_readfile):
        osinfo = ha_env.get_os_info()
        self.assertEqual(osinfo['ID'], 'debian')

    @patch(
        "ha_mqtt_pi_smbus.environ.get_command_data",
        return_value="up 20 hours, 57 minutes"
    )
    def test_get_uptime(self, mock_readfile):
        uptime = ha_env.get_uptime()
        self.assertEqual(uptime, 'up 20 hours, 57 minutes')

    @patch(
        "ha_mqtt_pi_smbus.environ.get_command_data",
        return_value="2025-08026 17:42:54"
    )
    def test_get_last_restart(self, mock_readfile):
        last_restart = ha_env.get_last_restart()
        self.assertEqual(last_restart, '2025-08026 17:42:54')

    @patch(
        "ha_mqtt_pi_smbus.environ.get_command_data",
        return_value="""
            eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:18  txqueuelen 1000  (Ethernet)
        """,
    )
    def test_mac_address_eth_success(self, mock_getcmd):
        mac = ha_env.get_mac_address_by_interface("eth0")
        self.assertEqual(mac, "b8:27:eb:94:a7:18")

    @patch(
        "ha_mqtt_pi_smbus.environ.get_command_data",
        return_value="""
            wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:19  txqueuelen 1000  (Ethernet)
        """,
    )
    def test_mac_address_wlan_success(self, mock_getcmd):
        mac = ha_env.get_mac_address_by_interface("wlan0")
        self.assertEqual(mac, "b8:27:eb:94:a7:19")

    @patch(
        "ha_mqtt_pi_smbus.environ.get_command_data",
        side_effect=[
            None,
            """wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:19  txqueuelen 1000  (Ethernet)
        """,
        ],
    )
    def test_mac_address_fake_except(self, mock_getcmd):
        mac = ha_env.get_mac_address_by_interface("fake0")
        self.assertIsNone(mac)

    @patch(
        "ha_mqtt_pi_smbus.environ.get_command_data",
        side_effect=[
            """eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:19  txqueuelen 1000  (Ethernet)
        """,
        ],
    )
    def test_mac_address_no_parm_but_eth(self, mock_getcmd):
        mac = ha_env.get_mac_address()
        self.assertEqual(mac, "b8:27:eb:94:a7:19")

    @patch(
        "ha_mqtt_pi_smbus.environ.get_command_data",
        side_effect=[
            None,
            """wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:19  txqueuelen 1000  (Ethernet)
        """,
        ],
    )
    def test_mac_address_no_parm_but_wlan(self, mock_getcmd):
        mac = ha_env.get_mac_address()
        self.assertEqual(mac, "b8:27:eb:94:a7:19")

    @patch(
        "ha_mqtt_pi_smbus.environ.get_command_data",
        side_effect=[
            None,
            """wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:19  txqueuelen 1000  (Ethernet)
        """,
        ],
    )
    def test_get_object_id(self, mock_getcmd):
        objectId = ha_env.get_object_id()
        self.assertEqual(objectId, "b827eb94a719")
    
    @patch(
            "ha_mqtt_pi_smbus.environ.readfile", return_value="""[project]
version = "v0.1.3"
""")
    def test_get_pyproject_version_normal(self, mock_readfile):
        version = ha_env.get_pyproject_version()
        mock_readfile.assert_called_once()
        self.assertEqual(version, "v0.1.3")
    
    @patch(
            "ha_mqtt_pi_smbus.environ.readfile", return_value="""[project]
""")
    def test_get_pyproject_version_none(self, mock_readfile):
        version = ha_env.get_pyproject_version()
        mock_readfile.assert_called_once()
        self.assertEqual(version, None)
    
    @patch( "ha_mqtt_pi_smbus.environ.get_command_data", return_value="v0.1.4")
    def test_get_setuptools_version_normal(self, mock_setuptools):
        version = ha_env.get_setuptools_version()
        mock_setuptools.assert_called_once()
        self.assertEqual(version, "v0.1.4")
    
    @patch( "ha_mqtt_pi_smbus.environ.get_command_data", return_value=None)
    def test_get_setuptools_version_none(self, mock_setuptools):
        version = ha_env.get_setuptools_version()
        mock_setuptools.assert_called_once()
        self.assertEqual(version, None)
    
    @patch("ha_mqtt_pi_smbus.environ.importlib.metadata.version", return_value="v0.1.5")
    def test_get_metadata_version_normal(self, mock_version):
        version = ha_env.get_metadata_version()
        mock_version.assert_called_once()
        self.assertEqual(version, "v0.1.5")
    
    @patch("ha_mqtt_pi_smbus.environ.importlib.metadata.version", side_effect=importlib.metadata.PackageNotFoundError)
    def test_get_metadata_version_none(self, mock_metadata):
        version = ha_env.get_metadata_version()
        mock_metadata.assert_called_once()
        self.assertEqual(version, None)
    
    @patch("ha_mqtt_pi_smbus.__version__", "v0.1.6")
    def test_get_package_version_normal(self):
        version = ha_env.get_package_version()
        self.assertEqual(version, "v0.1.6")
    
    def test_get_package_version_error(self):
        pkg = sys.modules["ha_mqtt_pi_smbus"]
        saved = getattr(pkg, "__version__", None)

        # Remove __version__ temporarily
        if "__version__" in pkg.__dict__:
            del pkg.__dict__["__version__"]

        try:
            version = ha_env.get_package_version()
            self.assertIsNone(version)
        finally:
            # Restore so other tests don’t break
            if saved is not None:
                pkg.__version__ = saved

    @patch( "ha_mqtt_pi_smbus.environ.get_package_version", return_value=None)
    @patch( "ha_mqtt_pi_smbus.environ.get_metadata_version", return_value=None)
    @patch( "ha_mqtt_pi_smbus.environ.get_setuptools_version", return_value=None)
    @patch( "ha_mqtt_pi_smbus.environ.get_pyproject_version", return_value=None)
    def test_get_my_version_default(self, mock_pyproject, mock_setuptools, mock_metadata, mock_package):
        version = ha_env.get_my_version()
        mock_pyproject.assert_called_once()
        mock_setuptools.assert_called_once()
        mock_metadata.assert_called_once()
        mock_package.assert_called_once()
        self.assertEqual(version, "0.0.0-dev")

    @patch("ha_mqtt_pi_smbus.__version__", "v0.1.6")
    @patch( "ha_mqtt_pi_smbus.environ.get_metadata_version", return_value=None)
    @patch( "ha_mqtt_pi_smbus.environ.get_setuptools_version", return_value=None)
    @patch( "ha_mqtt_pi_smbus.environ.get_pyproject_version", return_value=None)
    def test_get_my_version_package(self, mock_pyproject, mock_setuptools, mock_metadata):
        version = ha_env.get_my_version()
        mock_pyproject.assert_called_once()
        mock_setuptools.assert_called_once()
        mock_metadata.assert_called_once()
        self.assertEqual(version, "v0.1.6")

    @patch("ha_mqtt_pi_smbus.environ.importlib.metadata.version", return_value="v0.1.5")
    @patch( "ha_mqtt_pi_smbus.environ.get_setuptools_version", return_value=None)
    @patch( "ha_mqtt_pi_smbus.environ.get_pyproject_version", return_value=None)
    def test_get_my_version_metadata(self, mock_pyproject, mock_setuptools, mock_metadata):
        version = ha_env.get_my_version()
        mock_pyproject.assert_called_once()
        mock_setuptools.assert_called_once()
        mock_metadata.assert_called_once()
        self.assertEqual(version, "v0.1.5")

    @patch( "ha_mqtt_pi_smbus.environ.get_command_data", return_value="v0.1.4")
    @patch( "ha_mqtt_pi_smbus.environ.get_pyproject_version", return_value=None)
    def test_get_my_version_setuptools(self, mock_pyproject, mock_setuptools):
        version = ha_env.get_my_version()
        mock_pyproject.assert_called_once()
        mock_setuptools.assert_called_once()
        self.assertEqual(version, "v0.1.4")

    @patch(
            "ha_mqtt_pi_smbus.environ.readfile", return_value="""[project]
version = "v0.1.3"
""")
    def test_get_my_version_pyproject(self, mock_pyproject):
        version = ha_env.get_my_version()
        mock_pyproject.assert_called_once()
        self.assertEqual(version, "v0.1.3")
