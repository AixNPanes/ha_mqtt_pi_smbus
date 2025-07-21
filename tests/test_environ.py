# tests/test_routes.py
from argparse import Namespace
import pytest
import subprocess
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch

from ha_mqtt_pi_smbus.environ import (
    getTemperature,
    getMacAddress,
    getMacAddressByInterface,
    getObjectId,
    getCpuInfo,
    getOSInfo,
)

from .mock_data import *


class TestDevice(unittest.TestCase):
    def setUp(self):
        parser = Namespace(
            logginglevel="DEBUG", title="Test Title", subtitle="Test Subtitle"
        )

        self.mocked_open = MOCKED_OPEN

    def test_temperature(self):
        with patch("builtins.open", self.mocked_open):
            print("CpuInfo():")
            print(getCpuInfo())
            print(getCpuInfo()["cpu"]["Model"])
            print("OSInfo():")
            print(getOSInfo())
            temp = getTemperature()
            assert temp == 46.16

    def test_mac_address_eth_success(self):
        fake_ifconfig_output = """
            eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:18  txqueuelen 1000  (Ethernet)
        """
        with patch(
            "ha_mqtt_pi_smbus.environ.subprocess.check_output",
            return_value=fake_ifconfig_output.encode("utf-8"),
        ):
            mac = getMacAddressByInterface("eth0")
            assert mac == "b8:27:eb:94:a7:18"

    def test_mac_address_wlan_success(self):
        fake_ifconfig_eth0_output = """
            eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:18  txqueuelen 1000  (Ethernet)
        """
        fake_ifconfig_wlan0_output = """
            wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:19  txqueuelen 1000  (Ethernet)
        """
        with patch(
            "ha_mqtt_pi_smbus.environ.subprocess.check_output",
            return_value=fake_ifconfig_eth0_output.encode("utf-8"),
        ):
            mac = getMacAddressByInterface("eth0")
            assert mac == "b8:27:eb:94:a7:18"
        with patch(
            "ha_mqtt_pi_smbus.environ.subprocess.check_output",
            return_value=fake_ifconfig_wlan0_output.encode("utf-8"),
        ):
            mac = getMacAddressByInterface("wlan0")
            assert mac == "b8:27:eb:94:a7:19"

    def test_mac_address_fake_except(self):
        with patch(
            "ha_mqtt_pi_smbus.environ.subprocess.check_output"
        ) as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(
                1, ["ifconfig", "fake0"]
            )
            mac = getMacAddressByInterface("fake0")
            assert mac is None

    def test_mac_address_wlan0(self):
        fake_ifconfig_wlan0_output = """
            wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:19  txqueuelen 1000  (Ethernet)
        """.encode(
            "utf-8"
        )
        with patch(
            "ha_mqtt_pi_smbus.environ.subprocess.check_output",
            side_effect=["".encode("utf-8"), fake_ifconfig_wlan0_output],
        ) as mock_check_output:
            mac = getMacAddress()
            assert mac == "b8:27:eb:94:a7:19"

    def test_objectid(self):
        fake_ifconfig_output = """
            eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            ether b8:27:eb:94:a7:18  txqueuelen 1000  (Ethernet)
        """
        with patch(
            "ha_mqtt_pi_smbus.environ.subprocess.check_output",
            return_value=fake_ifconfig_output.encode("utf-8"),
        ):
            id = getObjectId()
            assert id == "b827eb94a718"

    def test_cpuinfo(self):
        with patch("builtins.open", self.mocked_open):
            cpu = getCpuInfo()
            assert "cpu" in cpu
            assert cpu["cpu"]["Revision"] == "a22082"

    def test_osinfo(self):
        with patch("builtins.open", self.mocked_open):
            osinf = getOSInfo()
            assert osinf["ID"] == "debian"
