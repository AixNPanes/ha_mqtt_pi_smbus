# tests/test_routes.py
import unittest
from unittest.mock import MagicMock, patch
from mqtt_client import State
from web_server import HAFlask
from argparse import Namespace

class TestHAFlask(unittest.TestCase):

    def setUp(self):
        # Mock MQTTClient and HADevice
        self.mock_client = MagicMock()
        self.mock_device = MagicMock()

        # Simulate MQTT connection behavior
        self.mock_client.is_connected.return_value = False
        self.mock_client.connect_mqtt.return_value = None
        self.mock_client.loop_start.return_value = None

        parser = Namespace(
            logginglevel='DEBUG',
            title='Test Title',
            subtitle='Test Subtitle'
        )

        self.app = HAFlask(__name__, parser, self.mock_client, self.mock_device)
        self.client = self.app.test_client()

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Title', response.data)

    def test_mqtt_toggle_connect_without_connected_with_is_connection(self):
        # State before toggle: disconnected
        self.mock_client.is_connected.side_effect = [True]
        payload = {
            'Connected': False,
            'Discovered': False,
            'rc': None,
            'Error': []
        }

        response = self.client.post('/mqtt-toggle', json=payload)
        self.assertEqual(self.mock_client.is_connected.call_count, 1)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(json_data['Error'][0], 'Web page reloaded, resyncing state')
        self.mock_client.connect_mqtt.assert_not_called()
        self.mock_client.loop_start.assert_not_called()

    def test_mqtt_toggle_connect_with_connected_without_is_connection(self):
        # State before toggle: disconnected
        self.mock_client.is_connected.side_effect = [False]
        payload = {
            'Connected': True,
            'Discovered': False,
            'rc': None,
            'Error': []
        }

        response = self.client.post('/mqtt-toggle', json=payload)
        self.assertEqual(self.mock_client.is_connected.call_count, 1)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertFalse(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(json_data['Error'][0], 'Web page reloaded, resyncing state')
        self.mock_client.connect_mqtt.assert_not_called()
        self.mock_client.loop_start.assert_not_called()

    def test_mqtt_toggle_connect_without_connected_without_is_connection(self):
        # State before toggle: disconnected
        self.mock_client.is_connected.side_effect = [False] * 21
        payload = {
            'Connected': False,
            'Discovered': False,
            'rc': None,
            'Error': []
        }

        response = self.client.post('/mqtt-toggle', json=payload)
        self.assertEqual(self.mock_client.is_connected.call_count, 21)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(len(json_data['Error']), 0)
        self.mock_client.connect_mqtt.assert_called_once()
        self.mock_client.loop_start.assert_called_once()

    def test_mqtt_toggle_connect_with_connected_with_is_connection(self):
        # State before toggle: disconnected
        self.mock_client.is_connected.side_effect = [True] * 21
        payload = {
            'Connected': True,
            'Discovered': False,
            'rc': None,
            'Error': []
        }

        response = self.client.post('/mqtt-toggle', json=payload)
        self.assertEqual(self.mock_client.is_connected.call_count, 1)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertFalse(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(len(json_data['Error']), 0)
        self.mock_client.connect_mqtt.assert_not_called()
        self.mock_client.loop_start.assert_not_called()

    def test_discovery_toggle_without_connection(self):
        self.mock_client.is_connected.return_value = False
        input_state = State()
        input_state.connected = False
        input_state.discovered = False
        self.mock_client.state = input_state
        payload = {
            'Connected': False,
            'Discovered': False,
            'rc': None,
            'Error': []
        }

        response = self.client.post('/discovery-toggle', json=payload)
        self.assertEqual(response.status_code, 200)
        print(response.get_json())
        json_data = response.get_json()
        self.assertFalse(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(len(json_data['Error']), 1)
        self.assertEqual(json_data['Error'][0], 'client must be connected')

    def test_discovery_toggle_connection_inconsistency_with_is_connected_false(self):
        self.mock_client.is_connected.return_value = False
        input_state = State()
        input_state.connected = True
        self.mock_client.state = input_state
        payload = {
            'Connected': True,
            'Discovered': False,
            'rc': None,
            'Error': []
        }

        response = self.client.post('/discovery-toggle', json=payload)
        self.assertEqual(response.status_code, 200)
        print(response.get_json())
        json_data = response.get_json()
        self.assertEqual(len(json_data['Error']), 1)
        self.assertEqual(json_data['Error'][0], 'client connected state mismatch')
        self.assertTrue(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)

    def test_discovery_toggle_connection_inconsistency_with_is_connected_true(self):
        self.mock_client.is_connected.return_value = True
        input_state = State()
        input_state.connected = False
        self.mock_client.state = input_state
        payload = {
            'Connected': False,
            'Discovered': False,
            'rc': None,
            'Error': []
        }

        response = self.client.post('/discovery-toggle', json=payload)
        self.assertEqual(response.status_code, 200)
        print(response.get_json())
        json_data = response.get_json()
        self.assertEqual(len(json_data['Error']), 1)
        self.assertEqual(json_data['Error'][0], 'client connected state mismatch')
        self.assertFalse(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)

    def test_discovery_toggle_with_connection_with_undiscovered(self):
        self.mock_client.is_connected.return_value = True
        input_state = State()
        input_state.connected = True
        input_state.discovered = True
        self.mock_client.state = input_state
        payload = {
            'Connected': True,
            'Discovered': False,
            'rc': None,
            'Error': []
        }

        response = self.client.post('/discovery-toggle', json=payload)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(len(json_data['Error']), 0)

    def test_discovery_toggle_with_connection_with_discovered(self):
        self.mock_client.is_connected.return_value = True
        input_state = State()
        input_state.connected = True
        input_state.discovered = True
        self.mock_client.state = input_state
        payload = {
            'Connected': True,
            'Discovered': True,
            'rc': None,
            'Error': []
        }

        response = self.client.post('/discovery-toggle', json=payload)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['Connected'])
        self.assertFalse(json_data['Discovered'])
        self.assertEqual(json_data['rc'], None)
        self.assertEqual(len(json_data['Error']), 0)
