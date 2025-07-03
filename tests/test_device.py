# tests/test_routes.py
from argparse import Namespace
import pytest
import time
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch

from ha_mqtt_pi_smbus.device import HASensor, HADevice, SMBusDevice, SMBusDevice_Sampler_Thread

class Humidity(HASensor):
    def __init__(self):
        super().__init__('mbar')

class TestDevice(unittest.TestCase):
    def setUp(self):
        parser = Namespace(
            logginglevel='DEBUG',
            title='Test Title',
            subtitle='Test Subtitle'
        )

        self.smbus_device = SMBusDevice(bus=2)
        self.smbus_device.sample()
        self.ha_sensor = Humidity()
        self.ha_device = HADevice((
                Humidity(),
                Humidity()
            ),
            name='Test Device', state_topic='my/topic', manufacturer='manufact.', model='model1234')

    def test_ha_sensor(self):
        self.assertEqual(self.ha_sensor.name, 'humidity')
        self.assertEqual(self.ha_sensor.device_class, 'humidity')
        self.assertEqual(self.ha_sensor.discovery_payload['name'], 'humidity')
        self.assertEqual(self.ha_sensor.discovery_payload['device_class'], 'humidity')
        self.assertEqual(self.ha_sensor.discovery_payload['unit_of_meas'], 'mbar')
        self.assertEqual(self.ha_sensor.jsonPayload(), '{"name": "humidity", "stat_t": "", "device_class": "humidity", "val_tpl": "{{ value_json.humidity }}", "unit_of_meas": "mbar", "uniq_id": "b827ebc1f24d-humidity", "dev": {}}')

    def test_ha_device(self):
        self.assertEqual(len(self.ha_device.sensors), 1)
        with pytest.raises(Exception):
            self.ha_device.data()

    def test_smbus_device(self):
        self.assertEqual(self.smbus_device.bus, 2)
        self.assertEqual(self.smbus_device.data()['address'], 118)
        self.assertEqual(self.smbus_device.toJson(), '')
        self.assertEqual(str(self.smbus_device), 'bus: 2, address: 118')

    @patch('ha_mqtt_pi_smbus.device.SMBusDevice.sample')
    @patch('ha_mqtt_pi_smbus.device.SMBusDevice')
    def test_smbus_device_sampler_thread(self, mock_device, mock_sample):
        mock_sample.return_value = {'last_update': 2}
        thread = SMBusDevice_Sampler_Thread(mock_device, 1)
        thread.start()
        time.sleep(1)
        assert mock_sample()['last_update'] == 2
        thread.do_run = False
        thread.join()
