# tests/test_bme280_device.py
import datetime
import logging
from unittest import TestCase
from unittest.mock import patch


class TestDevice(TestCase):
    @patch("example.pi_bme280.device.BME280")
    @patch("ha_mqtt_pi_smbus.device.getCpuInfo", return_value={"cpu": {"Model": "B"}})
    @patch("ha_mqtt_pi_smbus.device.getObjectId", side_effect=["b827eb94a718"] * 10)
    def test_bmedevice_constructor(
        self, mock_getObjectId, mock_getCpuInfo, mock_bme280
    ):
        from example.pi_bme280.device import BME280_Device

        device = BME280_Device(
            "test", "bme280/state", "Bosch", "BME280", mock_bme280, 1, 119
        )
        mock_getObjectId.assert_called_once()
        mock_getCpuInfo.assert_called_once()
        self.assertEqual(len(device.sensors), 8)
        self.assertEqual(device.device.identifiers, ["test"])
        self.assertEqual(device.device.name, "test")
        self.assertEqual(device.device.manufacturer, "Bosch")
        self.assertEqual(device.device.model, "BME280")
        self.assertEqual(device.device.serial_number, "b827eb94a718")
        self.assertEqual(device.device.sw_version, "0.0.1")
        self.assertEqual(device.state_topic, "bme280/state")
        self.assertEqual(
            device.discovery_topic, "homeassistant/device/b827eb94a718/config"
        )
        self.assertEqual(device.qos, 0)

    @patch("ha_mqtt_pi_smbus.device.getCpuInfo", return_value={"cpu": {"Model": "B"}})
    @patch("ha_mqtt_pi_smbus.device.getObjectId", side_effect=["b827eb94a718"] * 10)
    @patch(
        "example.pi_bme280.device.BME280.getdata",
        return_value={"temperature": 99, "pressure": 1010, "humidity": 99},
    )
    @patch("example.pi_bme280.device.BME280")
    def test_bmedevice_data(
        self, mock_bme280, mock_getdata, mock_getObjectId, mock_getCpuInfo
    ):
        from example.pi_bme280.device import BME280_Device

        device = BME280_Device(
            "test", "bme280/state", "Bosch", "BME280", mock_bme280, 1, 119
        )
        data = device.getdata()
        mock_getdata.assert_called_once()
        self.assertTrue("temperature" in data)
        self.assertTrue("pressure" in data)
        self.assertTrue("humidity" in data)
        self.assertEqual(data["temperature"], 99)
        self.assertEqual(data["pressure"], 1010)
        self.assertEqual(data["humidity"], 99)

    @patch("ha_mqtt_pi_smbus.device.getCpuInfo", return_value={"cpu": {"Model": "B"}})
    @patch("bme280.sample")
    @patch("bme280.load_calibration_params", return_value=123.456)
    @patch("ha_mqtt_pi_smbus.device.SMBus")
    def test_bme280(self, mock_smbus, mock_calibration, mock_sample, mock_getCpuInfo):
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
        after = datetime.datetime.now()
        last_update = device.last_update
        self.assertLess(before, last_update)
        self.assertLess(last_update, after)
        mock_sample.assert_called_once()
        device.temperature = 1
        device.pressure = 2
        device.humidity = 3
        data = device.getdata()
        last_update_string = last_update.strftime("%m/%d/%Y %H:%M:%S")
        self.assertEqual(data["last_update"], last_update_string)
        self.assertEqual(data["temperature"], 1)
        self.assertEqual(data["pressure"], 2)
        self.assertEqual(data["humidity"], 3)
