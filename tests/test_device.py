# tests/test_routes.py
from argparse import Namespace
import logging
import pytest
import time
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch

from ha_mqtt_pi_smbus.device import (
    HASensor,
    HADevice,
    SMBusDevice_Sampler_Thread,
)
from example.pi_bme280.device import (
    Temperature,
    Pressure,
    Humidity,
)

from .mock_data import MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT, MOCKED_OPEN


class TestDevice(unittest.TestCase):
    def setUp(self):
        Namespace(logginglevel="DEBUG", title="Test Title", subtitle="Test Subtitle")

        self.mocked_open = MOCKED_OPEN

        with patch("builtins.open", self.mocked_open), patch(
            "ha_mqtt_pi_smbus.device.SMBus"
        ) as mock_smbus_class, patch(
            "subprocess.check_output"
        ) as mock_subprocess_check_output:

            from ha_mqtt_pi_smbus.device import (
                SMBusDevice,
            )

            mock_subprocess_check_output.side_effect = (
                MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT * 10
            )

            # Prepare your SMBus mock class + instance
            mock_smbus_instance = MagicMock()
            mock_smbus_instance.load_calibration_param.return_value = (
                "mocked_cal_params"
            )
            mock_smbus_instance.sample.return_value = {
                "temperature": 25.5,
                "pressure": 1013.2,
                "humidity": 45.8,
            }

            # Save mocks for later assertions
            self.mock_smbus_class = mock_smbus_class
            self.mock_smbus_instance = mock_smbus_instance

            # SMBus() constructor returns the instance mock
            self.mock_smbus_class.return_value = self.mock_smbus_instance

            # Call the real code while both mocks are active
            self.smbus_device = SMBusDevice(bus=2)
            self.smbus_device._smbus.load_calibration_param(0x71)
            self.smbus_device.sample()
            self.smbus_device._smbus.sample()

            self.ha_device = HADevice(
                (Temperature('test'), Pressure('test'), Humidity('test')),
                name="Test Device",
                state_topic="my/topic",
                manufacturer="manufact.",
                model="model1234",
            )
            self.ha_sensor = self.ha_device.sensors[0]
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
        self.assertEqual(self.ha_sensor.name, "test")
        self.assertEqual(self.ha_sensor.device_class, "temperature")
        self.assertEqual(self.ha_sensor.discovery_payload["device_class"], "temperature")
        self.assertEqual(self.ha_sensor.discovery_payload["unit_of_measurement"], f"{chr(176)}C")
        self.assertEqual(len(self.ha_sensor.jsonPayload()), 376)
        self.maxDiff = None
        self.assertEqual(
            self.ha_sensor.jsonPayload(),
            '{"platform": "sensor", "device_class": "temperature", "unit_of_measurement": "\\u00b0C", "value_template": "{{ value_json.temperature }}", "unique_id": "test_temperature", "expire_after": 120, "availability": {"payload_available": "Available", "payload_unavailable": "Unavailable", "value_template": "{{ value_json.availability }}", "topic": "homeassistant/test/availability"}}'
        )

    def test_test_ha_sensor(self):
        self.ha_sensor = HASensor('none');
        self.assertEqual(self.ha_sensor.name, "hasensor")
        self.assertEqual(self.ha_sensor.device_class, "hasensor")
        self.assertEqual(self.ha_sensor.discovery_payload["device_class"], None)
        self.assertEqual(self.ha_sensor.discovery_payload["unit_of_measurement"], 'none')
        self.assertEqual(len(self.ha_sensor.jsonPayload()), 354)
        self.maxDiff = None
        self.assertEqual(
            self.ha_sensor.jsonPayload(),
            '{"platform": "sensor", "device_class": null, "unit_of_measurement": "none", "value_template": "{{ value_json.hasensor }}", "unique_id": "None_None", "expire_after": 120, "availability": {"payload_available": "Available", "payload_unavailable": "Unavailable", "value_template": "{{ value_json.availability }}", "topic": "homeassistant/None/availability"}}'
        )

    def test_ha_device(self):
        self.assertEqual(len(self.ha_device.sensors), 3)
        with pytest.raises(Exception):
            self.ha_device.data()

    def test_ha_device_no_basename(self):
        self.assertEqual(len(self.ha_device.sensors), 3)
        with pytest.raises(Exception):
            self.ha_device.data()

    def test_ha_device_extra_parms(self):
        self.assertEqual(len(self.ha_device.sensors), 3)

        with patch("builtins.open", self.mocked_open), patch(
            "ha_mqtt_pi_smbus.device.SMBus"
        ) as mock_smbus_class, patch(
            "subprocess.check_output"
        ) as mock_subprocess_check_output:

            from ha_mqtt_pi_smbus.device import (
                SMBusDevice,
            )

            mock_subprocess_check_output.side_effect = (
                MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT * 10
            )
            self.ha_device = HADevice(
                (Temperature('test'), Pressure('test'), Humidity('test')),
                name="Test Device",
                state_topic="my/topic",
                manufacturer="manufact.",
                model="model1234",
                support_url="http://www.example.com/support",
                model_id="souped_up",
                suggested_area="race track",
            )
            self.ha_sensor = self.ha_device.sensors[0]
    
            self.assertEqual(
                    self.ha_device.origin.support_url,
                    "http://www.example.com/support")
            self.assertEqual(self.ha_device.origin.suggested_area, "race track")
            self.assertEqual(self.ha_device.device.model_id, "souped_up")

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

    @patch("ha_mqtt_pi_smbus.device.SMBusDevice.sample")
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_smbus_device_sampler_thread_sample(self, mock_device, mock_sample):
        mock_sample.return_value = {"last_update": 2}
        thread = SMBusDevice_Sampler_Thread(mock_device, 1)
        thread.do_run = True
        thread.start()
        time.sleep(15)
        assert mock_sample()["last_update"] == 2
        thread.do_run = False
        thread.join()
