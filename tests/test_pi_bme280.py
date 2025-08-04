# tests/test_pi_bme280.py
from io import StringIO
import logging
import pytest
import sys
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch


class TestPiBME280(unittest.TestCase):
    def setUp(self):
        self.stdout_patch = patch("sys.stdout", new_callable=StringIO)
        self.mock_stdout = self.stdout_patch.start()

    def tearDown(self):
        self.stdout_patch.stop()

    def test_pi_bme280_normal(self):
        with (
                patch('example.pi_bme280.parsing.BME280Parser') as mock_parser,
                patch('example.pi_bme280.device.BME280') as mock_bme280,
                patch('example.pi_bme280.device.BME280_Device') as mock_device,
                patch('ha_mqtt_pi_smbus.mqtt_client.MQTTClient') as mock_client,
                patch('ha_mqtt_pi_smbus.web_server.HAFlask') as mock_flask,
                ):
            sys.modules.pop("example.pi_bme280.pi_bme280", None)
            from example.pi_bme280.pi_bme280 import main
            from example.pi_bme280.parsing import Parser
            main([])
            mock_parser.assert_called_once()
            mock_bme280.assert_called_once()
            mock_device.assert_called_once()
            mock_client.assert_called_once()
            mock_flask.assert_called_once()

    def test_pi_bme280_atexit(self):
        with (
                patch('example.pi_bme280.parsing.BME280Parser') as mock_parser,
                patch('example.pi_bme280.device.BME280') as mock_bme280,
                patch('example.pi_bme280.device.BME280_Device') as mock_device,
                patch('ha_mqtt_pi_smbus.mqtt_client.MQTTClient') as mock_client,
                patch('ha_mqtt_pi_smbus.web_server.HAFlask') as mock_flask,
                patch('atexit.register') as mock_atexit_register,
                ):
            sys.modules.pop("example.pi_bme280.pi_bme280", None)
            from example.pi_bme280.pi_bme280 import main, shutdown_server
            from example.pi_bme280.parsing import Parser

    def test_pi_bme280_shutdown(self):
        with (
                patch('example.pi_bme280.pi_bme280.app') as mock_app,
                ):
            mock_app.shutdown_server.return_value = 0
            from example.pi_bme280.pi_bme280 import main, shutdown_server, app
            shutdown_server()
            mock_app.shutdown_server.assert_called_once()

    @patch("ha_mqtt_pi_smbus.web_server.HAFlask")
    @patch("example.pi_bme280.device.BME280")
    @patch("example.pi_bme280.device.BME280_Device")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient")
    @patch("example.pi_bme280.parsing.BME280Parser")
    def test_pi_bme280_with_Exception(self, mock_parser, mock_client, mock_device, mock_bme280, mock_flask):
        mock_app = MagicMock()
        mock_app.run.side_effect=Exception("mock generic error")
        mock_flask.return_value = mock_app
        sys.modules.pop("example.pi_bme280.pi_bme280", None)
        from example.pi_bme280.pi_bme280 import main
        from example.pi_bme280.parsing import Parser
        main([])
        self.assertIn("mock generic error", self.mock_stdout.getvalue())
