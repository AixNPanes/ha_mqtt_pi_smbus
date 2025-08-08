# tests/test_mqtt_client.py
from argparse import Namespace
import datetime
import logging
import pytest
import unittest
from unittest import mock
from unittest.mock import patch, mock_open, MagicMock


class TestDevice(unittest.TestCase):
    def setUp(self):
        self.parser = Namespace(
            logginglevel="DEBUG", title="Test Title", subtitle="Test Subtitle"
        )

    def tearDown(self):
        pass

    @patch('ha_mqtt_pi_smbus.device.getOSInfo', return_value={'PRETTY_NAME':'Linux'})
    @patch('ha_mqtt_pi_smbus.device.getCpuInfo', return_value={'cpu':{'Model':'B'}})
    @patch('ha_mqtt_pi_smbus.device.getObjectId', side_effect=['b827eb94a718'] * 10)
    @patch('example.pi_bme280.device.BME280')
    @patch('ha_mqtt_pi_smbus.device.SMBusDevice')
    def test_bmedevice_constructor(self, mock_smbusDevice, mock_bme280, mock_getObjectIdi, mock_getCpuInfo, mock_getOSInfo):
        from example.pi_bme280.device import BME280_Device
        device = BME280_Device(
                'test',
                'bme280/state',
                'Bosch',
                'BME280',
                mock_bme280,
                1,
                119)
        self.assertEqual(len(device.sensors), 4)

    @patch('ha_mqtt_pi_smbus.device.getOSInfo', return_value={'PRETTY_NAME':'Linux'})
    @patch('ha_mqtt_pi_smbus.device.getCpuInfo', return_value={'cpu':{'Model':'B'}})
    @patch('ha_mqtt_pi_smbus.device.getObjectId', side_effect=['b827eb94a718'] * 10)
    @patch('example.pi_bme280.device.BME280') 
    @patch('ha_mqtt_pi_smbus.device.SMBusDevice')
    def test_bmedevice_data(self, mock_smbusDevice, mock_bme280, mock_getObjectId, mock_getCpuInfo, mock_getOSInfo):
        from example.pi_bme280.device import BME280_Device
        mock_bme280.data.return_value = {'temperature':99,'pressure':1010,'humidity':99}
        device = BME280_Device(
                'test',
                'bme280/state',
                'Bosch',
                'BME280',
                mock_bme280,
                1,
                119)
        data = device.getdata()
        self.assertTrue('temperature' in data)
        self.assertTrue('pressure' in data)
        self.assertTrue('humidity' in data)
        self.assertEqual(data['temperature'], 99)
        self.assertEqual(data['pressure'], 1010)
        self.assertEqual(data['humidity'], 99)

    def test_bme280(self):
        with (patch('ha_mqtt_pi_smbus.device.SMBus') as mock_SMBus, 
            patch('bme280.load_calibration_params', return_value=123.456) as mock_lcp,
            patch('bme280.sample') as mock_sample):
            from example.pi_bme280.device import BME280
            device = BME280(bus=2, address=0x77)
            self.assertEqual(device.bus, 2)
            self.assertEqual(device.address, 0x77)
            self.assertEqual(device.temperature, -17.77777777777778)
            self.assertEqual(device.pressure, 0)
            self.assertEqual(device.humidity, 0)
            self.assertEqual(device._calibration_params, 123.456)
            before = datetime.datetime.now()
            device.sample()
            last_update = device.last_update
            after = datetime.datetime.now()
            self.assertLess(before, last_update)
            self.assertLess(last_update, after)
            device.temperature = 1
            device.pressure = 2
            device.humidity = 3
            data = device.getdata()
            last_update_string = last_update.strftime("%m/%d/%Y %H:%M:%S")
            self.assertEqual(data['last_update'], last_update_string)
            self.assertEqual(data['temperature'], 1)
            self.assertEqual(data['pressure'], 2)
            self.assertEqual(data['humidity'], 3)
