# tests/test_pi_bme280.py
from io import StringIO
import sys
from unittest import TestCase
from unittest.mock import patch, MagicMock


class TestPiBME280(TestCase):
    def setUp(self):
        self.stdout_patch = patch("sys.stdout", new_callable=StringIO)
        self.mock_stdout = self.stdout_patch.start()

    def tearDown(self):
        self.stdout_patch.stop()

    @patch("example.pi_bme280.parsing.BME280Parser")
    @patch("example.pi_bme280.device.BME280")
    @patch("example.pi_bme280.device.BME280_Device")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient")
    @patch("ha_mqtt_pi_smbus.web_server.HAFlask")
    def test_pi_bme280_normal(
        self, mock_flask, mock_client, mock_device, mock_bme280, mock_parser
    ):
        sys.modules.pop("example.pi_bme280.pi_bme280", None)
        from example.pi_bme280.pi_bme280 import main

        main([])
        mock_parser.assert_called_once()
        mock_bme280.assert_called_once()
        mock_device.assert_called_once()
        mock_client.assert_called_once()
        mock_flask.assert_called_once()

    @patch("example.pi_bme280.parsing.BME280Parser")
    @patch("example.pi_bme280.device.BME280")
    @patch("example.pi_bme280.device.BME280_Device")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient")
    @patch("ha_mqtt_pi_smbus.web_server.HAFlask")
    @patch("atexit.register")
    def test_pi_bme280_atexit(
        self,
        mock_flask,
        mock_client,
        mock_device,
        mock_bme280,
        mock_parser,
        mock_atexit_register,
    ):
        sys.modules.pop("example.pi_bme280.pi_bme280", None)

    @patch("example.pi_bme280.pi_bme280.app")
    def test_pi_bme280_shutdown(self, mock_app):
        mock_app.shutdown_server.return_value = 0
        from example.pi_bme280.pi_bme280 import shutdown_server

        shutdown_server()
        mock_app.shutdown_server.assert_called_once()

    @patch("ha_mqtt_pi_smbus.web_server.HAFlask")
    @patch("example.pi_bme280.device.BME280")
    @patch("example.pi_bme280.device.BME280_Device")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient")
    @patch("example.pi_bme280.parsing.BME280Parser")
    def test_pi_bme280_with_Exception(
        self, mock_parser, mock_client, mock_device, mock_bme280, mock_flask
    ):
        mock_app = MagicMock()
        mock_app.run.side_effect = Exception("mock generic error")
        mock_flask.return_value = mock_app
        sys.modules.pop("example.pi_bme280.pi_bme280", None)
        from example.pi_bme280.pi_bme280 import main

        main([])
        self.assertIn("mock generic error", self.mock_stdout.getvalue())
