# tests/test_routes.py
from argparse import Namespace
import pytest
import time
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch, mock_open

from ha_mqtt_pi_smbus.device import (
    HASensor,
    HADevice,
    SMBusDevice_Sampler_Thread,
)
from .mock_data import *

class Humidity(HASensor):
    def __init__(self):
        super().__init__("mbar")


class TestDevice(unittest.TestCase):
    def setUp(self):
        parser = Namespace(
            logginglevel="DEBUG", title="Test Title", subtitle="Test Subtitle"
        )

        self.mocked_open = MOCKED_OPEN

        mock_ifconfig_eth0_data = MOCK_IFCONFIG_ETH0_DATA.encode('utf-8')
        mock_ifconfig_wlan0_data = MOCK_IFCONFIG_WLAN0_DATA.encode('utf-8')

        with patch("builtins.open", self.mocked_open), \
            patch("ha_mqtt_pi_smbus.device.SMBus") as mock_smbus_class, \
            patch("subprocess.check_output") as mock_subprocess_check_output:

            from ha_mqtt_pi_smbus.device import (
                SMBusDevice,
            )

            mock_subprocess_check_output.side_effect = [
                mock_ifconfig_eth0_data,
                mock_ifconfig_wlan0_data,
                mock_ifconfig_eth0_data,
                mock_ifconfig_wlan0_data,
                mock_ifconfig_eth0_data,
                mock_ifconfig_wlan0_data,
                mock_ifconfig_eth0_data,
                mock_ifconfig_wlan0_data,
                mock_ifconfig_eth0_data,
                mock_ifconfig_wlan0_data,
                mock_ifconfig_eth0_data,
                mock_ifconfig_wlan0_data,
                mock_ifconfig_eth0_data,
                mock_ifconfig_wlan0_data,
                mock_ifconfig_eth0_data,
                mock_ifconfig_wlan0_data,
                mock_ifconfig_eth0_data,
                mock_ifconfig_wlan0_data,
                mock_ifconfig_eth0_data,
                mock_ifconfig_wlan0_data,
                mock_ifconfig_eth0_data,
                mock_ifconfig_wlan0_data,
                mock_ifconfig_eth0_data,
                mock_ifconfig_wlan0_data,
            ]

            # Prepare your SMBus mock class + instance
            mock_smbus_instance = MagicMock()
            mock_smbus_instance.load_calibration_param.return_value = "mocked_cal_params"
            mock_smbus_instance.sample.return_value = {
                "temperature": 25.5,
                "pressure": 1013.2,
                "humidity": 45.8
            }

            # Save mocks for later assertions
            self.mock_smbus_class = mock_smbus_class
            self.mock_smbus_instance = mock_smbus_instance

            # SMBus() constructor returns the instance mock
            self.mock_smbus_class.return_value = self.mock_smbus_instance
        
            # Call the real code while both mocks are active
            self.smbus_device = SMBusDevice(bus=2)
            self.smbus_device._smbus.load_calibration_param(0x71)
            self.smbus_device._smbus.sample()

            self.ha_sensor = Humidity()
            self.ha_device = HADevice(
                (Humidity(), Humidity()),
                name="Test Device",
                state_topic="my/topic",
                manufacturer="manufact.",
                model="model1234",
            )
            # SMBus constructor called with bus=2
            mock_smbus_class.assert_called_once_with(2)
    
            # load_calibration_param called with correct address
            mock_smbus_instance.load_calibration_param.assert_called()
    
            # sample called with address & calibration params
            mock_smbus_instance.sample.assert_called()
    
            # Check the output from sample
            data = self.smbus_device._smbus.sample()
            self.assertEqual(data["temperature"], 25.5)    

        # Inline check
        self.mocked_open.assert_any_call("/proc/cpuinfo", mock.ANY)
        self.mocked_open.assert_any_call("/etc/os-release", mock.ANY)

    def tearDown(self):
        pass
    
    def xtest_smbus_methods(self):
        # SMBus constructor called with bus=2
        self.mock_smbus_class.assert_called_once_with(2)

        # load_calibration_param called with correct address
        self.mock_smbus_instance.load_calibration_param.assert_called()

        # sample called with address & calibration params
        self.mock_smbus_instance.sample.assert_called()

        # Check the output from sample
        data = self.device.sample()
        self.assertEqual(data["temperature"], 25.5)    

    def test_ha_sensor(self):
        self.assertEqual(self.ha_sensor.name, "humidity")
        self.assertEqual(self.ha_sensor.device_class, "humidity")
        self.assertEqual(self.ha_sensor.discovery_payload["name"], "humidity")
        self.assertEqual(self.ha_sensor.discovery_payload["device_class"], "humidity")
        self.assertEqual(self.ha_sensor.discovery_payload["unit_of_meas"], "mbar")
        self.assertEqual(
            self.ha_sensor.jsonPayload(),
            '{"name": "humidity", "stat_t": "", "device_class": "humidity", "val_tpl": "{{ value_json.humidity }}", "unit_of_meas": "mbar", "uniq_id": "b827ebc1f24d-humidity", "dev": {}}',
        )

    def test_ha_device(self):
        self.assertEqual(len(self.ha_device.sensors), 1)
        with pytest.raises(Exception):
            self.ha_device.data()

    def test_smbus_device(self):
        self.assertEqual(self.smbus_device.bus, 2)
        self.assertEqual(self.smbus_device.data()["address"], 118)
        self.assertEqual(self.smbus_device.toJson(), "")
        self.assertEqual(str(self.smbus_device), "bus: 2, address: 118")

    @patch("ha_mqtt_pi_smbus.device.SMBusDevice.sample")
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_smbus_device_sampler_thread(self, mock_device, mock_sample):
        mock_sample.return_value = {"last_update": 2}
        thread = SMBusDevice_Sampler_Thread(mock_device, 1)
        thread.start()
        time.sleep(1)
        assert mock_sample()["last_update"] == 2
        thread.do_run = False
        thread.join()
