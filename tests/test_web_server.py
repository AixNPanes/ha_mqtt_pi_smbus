# tests/test_web_server.py
import logging
from unittest import TestCase
from unittest.mock import MagicMock

from ha_mqtt_pi_smbus.config import Config
from ha_mqtt_pi_smbus.state import State
from ha_mqtt_pi_smbus.web_server import HAFlask


class TestHAFlask(TestCase):
    def setUp(self):
        config = Config({
            'title': 'Test Title',
            'subtitle': 'Test Subtitle',
            'mqtt': {
                'auto_discover': True,
                },
            })

        # Mock MQTTClient and HADevice
        self.mock_client = MagicMock()
        self.mock_device = MagicMock()
        self.mock_state = State()
        self.payload = {
            'Connected': False,
            'Discovered': False,
            'rc': None,
            'Errorcode': [],
            'Error': [],
        }

        # Simulate MQTT connection behavior
        self.mock_client.is_connected.return_value = False
        self.mock_client.connect_mqtt.return_value = None
        self.mock_client.loop_start.return_value = None
        self.mock_client.state = self.mock_state
        self.app = HAFlask(__name__, config, self.mock_client, self.mock_device, 3)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.logger = logging.getLogger('TestHAFlask')

    def test_index_normal(self):
        self.mock_client.is_connected.return_value = True
        with self.client.get('/', content_type='text/plain') as response:
            self.logger.debug(response)
            # response = self.app.dispatch_request()
            self.assertIn(b'Test Title', response.data)
            self.assertIn(b'Not Connected', response.data)
            self.assertIn(b'Not Discovered', response.data)

    def test_index_not_equal(self):
        self.mock_client.is_connected.return_value = False
        with self.app.test_request_context('/', method='GET'):
            response = self.app.dispatch_request()
            self.assertIn('Test Title', response)
            self.assertIn('Not Connected', response)
            self.assertIn('Not Discovered', response)

    def test_status(self):
        self.mock_client.is_connected.return_value = False
        with self.app.test_request_context('/status', method='GET'):
            response = self.app.dispatch_request()
            self.assertIsNotNone(response)

    def test_mqtt_toggle_not_connected(self):
        # State before toggle: disconnected
        self.mock_client.is_connected.side_effect = [False] * 4
        self.mock_client.state = State(
            {'Connected': False, 'Discovered': False, 'rc': None, 'Error': []}
        )
        payload = {'Connected': False, 'Discovered': False, 'rc': None, 'Error': []}

        response = self.client.post('/mqtt-toggle', json=payload)
        self.assertEqual(self.mock_client.is_connected.call_count, 7)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertFalse(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(len(json_data['Error']), 0)
        self.mock_client.connect_mqtt.assert_called()
        self.mock_client.loop_start.assert_called()

    def test_mqtt_toggle_connected(self):
        # State before toggle: disconnected
        self.mock_client.is_connected.side_effect = [True] * 4
        self.mock_client.state = State(
            {'Connected': True, 'Discovered': False, 'rc': None, 'Error': []}
        )
        payload = {'Connected': True, 'Discovered': False, 'rc': None, 'Error': []}

        response = self.client.post('/mqtt-toggle', json=payload)
        self.assertEqual(self.mock_client.is_connected.call_count, 4)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertFalse(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(len(json_data['Error']), 0)
        self.mock_client.connect_mqtt.assert_called()
        self.mock_client.loop_start.assert_called()

    def test_mqtt_toggle_timeout(self):
        # State before toggle: disconnected
        self.mock_client.is_connected.side_effect = [False] * 14
        self.mock_client.state = State(
            {'Connected': False, 'Discovered': False, 'rc': None, 'Error': []}
        )
        payload = {'Connected': False, 'Discovered': False, 'rc': None, 'Error': []}

        response = self.client.post('/mqtt-toggle', json=payload)
        self.assertEqual(self.mock_client.is_connected.call_count, 7)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertFalse(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(len(json_data['Error']), 0)
        self.mock_client.connect_mqtt.assert_called()
        self.mock_client.loop_start.assert_called()

    def test_mqtt_toggle_connect(self):
        # State before toggle: disconnected
        self.mock_client.is_connected.side_effect = [False, False, True, True]
        self.mock_client.state = State(
            {'Connected': False, 'Discovered': False, 'rc': None, 'Error': []}
        )
        payload = {'Connected': False, 'Discovered': False, 'rc': None, 'Error': []}

        response = self.client.post('/mqtt-toggle', json=payload)
        self.assertEqual(self.mock_client.is_connected.call_count, 6)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(len(json_data['Error']), 0)
        self.mock_client.connect_mqtt.assert_called()
        self.mock_client.loop_start.assert_called()

    def test_discovery_toggle_with_undiscovered(self):
        self.mock_client.is_connected.return_value = True
        input_state = State({'Connected': True, 'Discovered': False})
        self.mock_client.state = input_state
        payload = {'Connected': True, 'Discovered': False, 'rc': None, 'Error': []}

        response = self.client.post('/discovery-toggle', json=payload)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['Connected'])
        self.assertTrue(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(len(json_data['Error']), 0)

    def test_discovery_toggle_with_discovered(self):
        self.mock_client.is_connected.return_value = True
        input_state = State({'Connected': True, 'Discovered': True})
        input_state.connected = True
        input_state.discovered = True
        self.mock_client.state = input_state
        payload = {'Connected': True, 'Discovered': True, 'rc': None, 'Error': []}

        response = self.client.post('/discovery-toggle', json=payload)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(len(json_data['Error']), 0)

    def test_shutdown_with_not_connected(self):
        payload = {
            'Connected': False,
            'Discovered': False,
            'rc': 0,
            'Errorcode': [],
            'Error': [],
        }
        input_state = State(payload)
        self.mock_client.state = input_state
        self.mock_client.is_connected.return_value = input_state.connected

        self.app.shutdown_server()
        self.logger.debug('%s', self.mock_client.state.to_dict())
        self.assertFalse(self.mock_client.state.connected)
        self.assertFalse(self.mock_client.state.discovered)
        self.assertEqual(self.mock_client.state.rc, 0)
        self.assertEqual(len(self.mock_client.state.error), 0)
        self.assertEqual(len(self.mock_client.state.error_code), 0)

    def test_shutdown_with_connected_and_not_discovered(self):
        payload = {
            'Connected': True,
            'Discovered': False,
            'rc': 0,
            'Errorcode': [],
            'Error': [],
        }
        input_state = State(payload)
        self.mock_client.state = input_state
        self.mock_client.is_connected.return_value = input_state.connected

        self.app.shutdown_server()
        self.logger.debug('%s', self.mock_client.state.to_dict())
        self.assertFalse(self.mock_client.state.connected)
        self.assertFalse(self.mock_client.state.discovered)
        self.assertEqual(self.mock_client.state.rc, 0)
        self.assertEqual(len(self.mock_client.state.error), 0)
        self.assertEqual(len(self.mock_client.state.error_code), 0)

    def test_shutdown_with_connected_and_discovered(self):
        payload = {
            'Connected': True,
            'Discovered': True,
            'rc': 0,
            'Errorcode': [],
            'Error': [],
        }
        input_state = State(payload)
        self.mock_client.state = input_state
        self.mock_client.is_connected.return_value = input_state.connected

        self.app.shutdown_server()
        self.logger.debug('%s', self.mock_client.state.to_dict())
        self.assertFalse(self.mock_client.state.connected)
        self.assertFalse(self.mock_client.state.discovered)
        self.assertEqual(self.mock_client.state.rc, 0)
        self.assertEqual(len(self.mock_client.state.error), 0)
        self.assertEqual(len(self.mock_client.state.error_code), 0)
