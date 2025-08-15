# tests/test_devices.py
import datetime
import logging
import time
from unittest import TestCase
from unittest.mock import patch

from .mock_data import MOCK_CPUINFO_DATA

FAKE_TIME = datetime.datetime(2020, 1, 1, 1, 23, 45)

class MockDatetime:
    @classmethod
    def now(cls):
        return FAKE_TIME

CPUINFO = {
        "cpu": {
            "Model": "1234",
            }
        }

class TestDevice(TestCase):
    @patch('ha_mqtt_pi_smbus.environ.getObjectId', return_value='0123456789abcdef')
    @patch('ha_mqtt_pi_smbus.environ.getCpuInfo', return_value=CPUINFO)
    def test_ha_sensor_base(self, mock_cpuinfo, mock_objectid):
        from ha_mqtt_pi_smbus.device import ( HASensor, HADevice, SMBusDevice_Sampler_Thread,)
        from ha_mqtt_pi_smbus.environ import getCpuInfo
        from example.pi_bme280.device import ( Temperature, Pressure, Humidity,)
        ha_sensor = Temperature('test')
        self.assertEqual(ha_sensor.name, "test")
        self.assertEqual(ha_sensor.device_class, "temperature")
        self.assertEqual(ha_sensor.discovery_payload["device_class"], "temperature")
        self.assertEqual(ha_sensor.discovery_payload["unit_of_measurement"], f"{chr(176)}C")
        self.assertEqual(len(ha_sensor.jsonPayload()), 378)
        self.assertEqual(
            ha_sensor.jsonPayload(),
            '{"platform": "sensor", "device_class": "temperature", "unique_id": "test_temperature", "expire_after": 120, "unit_of_measurement": "\\u00b0C", "value_template": "{{ value_json.temperature }}", "availability": {"payload_available": "Available", "payload_not_available": "Unavailable", "value_template": "{{ value_json.availability }}", "topic": "homeassistant/test/availability"}}'
        )

    @patch('ha_mqtt_pi_smbus.environ.getObjectId', return_value='0123456789abcdef')
    @patch('ha_mqtt_pi_smbus.environ.getCpuInfo', return_value=CPUINFO)
    def test_ha_sensor_no_name(self, mock_cpuinfo, mock_objectid):
        from ha_mqtt_pi_smbus.device import ( HASensor, HADevice, SMBusDevice_Sampler_Thread,)
        from ha_mqtt_pi_smbus.environ import getCpuInfo
        from example.pi_bme280.device import ( Temperature, Pressure, Humidity,)
        ha_sensor = Temperature()
        self.assertEqual(ha_sensor.name, "temperature")

    @patch('ha_mqtt_pi_smbus.device.getObjectId', return_value='0123456789abcdef')
    @patch('ha_mqtt_pi_smbus.environ.readfile', return_value=MOCK_CPUINFO_DATA)
    def test_ha_device_base(self, mock_cpuinfo, mock_objectid):
        from ha_mqtt_pi_smbus.device import ( HASensor, HADevice, SMBusDevice_Sampler_Thread,)
        from ha_mqtt_pi_smbus.environ import getCpuInfo
        from example.pi_bme280.device import ( Temperature, Pressure, Humidity,)
        ha_device = HADevice(
            [Temperature('test')],
            name='Test device',
            state_topic='my/topic',
            manufacturer='manufact.',
            model='model1234',
            )
        self.assertEqual(ha_device.sensors[0].name, "test")
        self.assertEqual(ha_device.sensors[0].device_class, "temperature")
        self.assertEqual(ha_device.sensors[0].discovery_payload["device_class"], "temperature")
        self.assertEqual(ha_device.sensors[0].discovery_payload["unit_of_measurement"], f"{chr(176)}C")
        self.assertEqual(len(ha_device.sensors[0].jsonPayload()), 378)
        self.assertEqual(
            ha_device.sensors[0].jsonPayload(),
            '{"platform": "sensor", "device_class": "temperature", "unique_id": "test_temperature", "expire_after": 120, "unit_of_measurement": "\\u00b0C", "value_template": "{{ value_json.temperature }}", "availability": {"payload_available": "Available", "payload_not_available": "Unavailable", "value_template": "{{ value_json.availability }}", "topic": "homeassistant/test/availability"}}'
        )

    @patch('ha_mqtt_pi_smbus.device.getObjectId', return_value='0123456789abcdef')
    @patch('ha_mqtt_pi_smbus.environ.readfile', return_value=MOCK_CPUINFO_DATA)
    def test_ha_device_no_basename(self, mock_read, mock_getObjectId):
        from ha_mqtt_pi_smbus.device import HADevice
        from example.pi_bme280.device import Temperature
        ha_device = HADevice(
            [Temperature('test')],
            name='Test device',
            state_topic='my/topic',
            manufacturer='manufact.',
            model='model1234',
            )
        with self.assertRaises(Exception):
            ha_device.getdata()

    @patch('ha_mqtt_pi_smbus.device.getObjectId', return_value='0123456789abcdef')
    @patch('ha_mqtt_pi_smbus.environ.readfile', return_value=MOCK_CPUINFO_DATA)
    def test_ha_device_extra_parms(self, mock_cpu_info, mock_object_id):
        from ha_mqtt_pi_smbus.device import HADevice
        from example.pi_bme280.device import Temperature
        ha_device = HADevice(
            [Temperature('test')],
            name='Test device',
            state_topic='my/topic',
            manufacturer='manufact.',
            model='model1234',
            support_url='http://www.example.com/support',
            model_id='souped_up',
            suggested_area='race track',
            )
        self.assertEqual(
            ha_device.origin.support_url,
            'http://www.example.com/support')
        self.assertEqual(
            ha_device.device.model_id,
            'souped_up')
        self.assertEqual(
            ha_device.origin.suggested_area,
            "race track")

    @patch('ha_mqtt_pi_smbus.device.datetime.datetime', MockDatetime)
    @patch('ha_mqtt_pi_smbus.device.SMBus')
    def test_smbus_device_base(self, mock_smbus):
        from ha_mqtt_pi_smbus.device import SMBus, SMBusDevice
        smbus_device = SMBusDevice(bus=2, address=0x71)
        self.assertEqual(smbus_device.bus, 2)
        self.assertEqual(smbus_device.address, 113)
        self.assertEqual(smbus_device.getdata()['bus'], 2)
        self.assertEqual(smbus_device.getdata()['address'], 113)
        smbus_device.sample()
        data = smbus_device.getdata()
        self.assertEqual(data['last_update'], '01/01/2020 01:23:45')
        self.assertEqual(smbus_device.toJson(), '')
        self.assertEqual(str(smbus_device), 'bus: 2, address: 113')

    @patch('ha_mqtt_pi_smbus.device.SMBusDevice.sample', return_value = {'last_update': 2})
    @patch('ha_mqtt_pi_smbus.device.SMBusDevice')
    def test_smbus_device_sampler_thread_base(self, mock_device, mock_sample):
        from ha_mqtt_pi_smbus.device import SMBus, SMBusDevice, SMBusDevice_Sampler_Thread
        thread = SMBusDevice_Sampler_Thread(mock_device, 1)
        thread.start()
        time.sleep(1)
        assert mock_sample()['last_update'] == 2
        thread.do_run = False
        thread.join()

    @patch('ha_mqtt_pi_smbus.device.SMBusDevice.sample', return_value = {'last_update': 2})
    @patch('ha_mqtt_pi_smbus.device.SMBusDevice')
    def test_smbus_device_sampler_thread_sample(self, mock_device, mock_sample):
        from ha_mqtt_pi_smbus.device import SMBus, SMBusDevice, SMBusDevice_Sampler_Thread
        thread = SMBusDevice_Sampler_Thread(mock_device, 1)
        thread.start()
        time.sleep(15)
        assert mock_sample()['last_update'] == 2
        thread.do_run = False
        thread.join()