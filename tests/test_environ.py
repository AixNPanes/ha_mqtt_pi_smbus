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


class MockOpen:
    builtin_open = open

    def open(self, *args, **kwargs):
        if args[0] == "/sys/class/thermal/thermal_zone0/temp":
            return mock.mock_open(read_data="12345")(*args, **kwargs)
        if args[0] == "/proc/cpuinfo":
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


class TestDevice(unittest.TestCase):
    def setUp(self):

        parser = Namespace(
            logginglevel="DEBUG", title="Test Title", subtitle="Test Subtitle"
        )
        self.osinfo = getOSInfo()

    @mock.patch("builtins.open", MockOpen().open)
    def test_temperature(self):
        temp = getTemperature()
        assert temp == 12.345

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

    @mock.patch("builtins.open", MockOpen().open)
    def test_cpuinfo(self):
        cpu = getCpuInfo()
        assert "cpu" in cpu
        assert cpu["cpu"]["Revision"] == "a22082"

    @mock.patch("builtins.open", MockOpen().open)
    def test_osinfo(self):
        osinf = getOSInfo()
        assert osinf["ID"] == "debian"
