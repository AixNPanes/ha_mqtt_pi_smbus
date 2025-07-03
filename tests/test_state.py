# tests/test_state.py
from argparse import Namespace
import logging
import pytest
from pytest_mock import MockerFixture
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch

from ha_mqtt_pi_smbus.state import State, StateErrorEnum

class TestState(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('validate')

    def test_state_init(self):
        state = State()
        self.assertFalse(state.connected)
        self.assertFalse(state.discovered)
        self.assertEqual(state.rc, None)
        self.assertEqual(len(state.error_code), 0)
        self.assertEqual(len(state.error), 0)

    def test_state_obj(self):
        obj = {'Connected': True, 'Discovered': True, 'rc': 0, 'Errorcode': [StateErrorEnum.CONNECTED_INCONSISTENT_1.code], 'Error': ['Error!']}
        state = State(obj)
        self.assertTrue(state.connected)
        self.assertTrue(state.discovered)
        self.assertEqual(state.rc, 0)
        self.assertEqual(len(state.error_code), 1)
        self.assertEqual(state.error_code[0], StateErrorEnum.CONNECTED_INCONSISTENT_1.code)
        self.assertIsInstance(state.error_code, list)
        self.assertEqual(len(state.error), 1)
        self.assertEqual(state.error[0], 'Error!')
        self.assertIsInstance(state.error, list)
        self.assertEqual(state.to_dict()['rc'], 0)

    def test_state_error_code_not_list_and_error_not_list(self):
        obj = {'Connected': True, 'Discovered': True, 'rc': 0, 'Errorcode': 0, 'Error': 'Error!'}
        state = State(obj)
        self.assertNotIsInstance(state.error, list)
        self.assertNotIsInstance(state.error_code, list)
        self.assertEqual(state.to_dict()['rc'], 0)
        self.assertEqual(state.error_code, 0)
        self.assertEqual(state.error, 'Error!')

    def test_state_add_error_code(self):
        obj = {'Connected': True, 'Discovered': True, 'rc': 0, 'Errorcode': [], 'Error': ['Error!']}
        state = State(obj)
        self.assertEqual(len(state.error), 1)
        self.assertEqual(state.error[0], 'Error!')
        state.add_error_code(StateErrorEnum.CONNECTED_INCONSISTENT_1.code)
        self.assertEqual(len(state.error_code), 1)
        self.assertEqual(state.error_code[0], StateErrorEnum.CONNECTED_INCONSISTENT_1.code)
        state.add_error_code(StateErrorEnum.CONNECTED_INCONSISTENT_2.code)
        self.assertEqual(len(state.error_code), 2)
        self.assertEqual(state.error_code[0], StateErrorEnum.CONNECTED_INCONSISTENT_1.code)
        self.assertEqual(state.error_code[1], StateErrorEnum.CONNECTED_INCONSISTENT_2.code)

    def test_state_connected_equal(self):
        init_state = State({'Connected': False})
        state = init_state.validate({'Connected': False}, False)
        self.assertEqual(len(state.error_code), 0)

        state = State({'Connected': True}).validate({'Connected': True}, True)
        self.assertEqual(len(state.error_code), 0)

    def test_state_connected_not_equal(self):
        init_state = State({'Connected': False})
        state = init_state.validate({'Connected': True}, False)
        self.assertEqual(len(state.error_code), 1)
        self.assertEqual(StateErrorEnum.CONNECTED_INCONSISTENT_1, state.error_code[0])

        state = init_state.validate({'Connected': True}, True)
        self.assertEqual(len(state.error_code), 2)
        self.assertEqual(StateErrorEnum.CONNECTED_INCONSISTENT_1, state.error_code[0])
        self.assertEqual(StateErrorEnum.CONNECTED_INCONSISTENT_2, state.error_code[1])

        state = init_state.validate({'Connected': False}, True)
        self.assertEqual(len(state.error_code), 2)
        self.assertEqual(StateErrorEnum.CONNECTED_INCONSISTENT_1, state.error_code[0])
        self.assertEqual(StateErrorEnum.CONNECTED_INCONSISTENT_2, state.error_code[1])

        init_state = State({'Connected': True})
        state = init_state.validate({'Connected': False}, False)
        self.assertEqual(len(state.error_code), 2)
        self.assertEqual(StateErrorEnum.CONNECTED_INCONSISTENT_1, state.error_code[0])
        self.assertEqual(StateErrorEnum.CONNECTED_INCONSISTENT_2, state.error_code[1])

        state = init_state.validate({'Connected': False}, True)
        self.assertEqual(len(state.error_code), 1)
        self.assertEqual(StateErrorEnum.CONNECTED_INCONSISTENT_1, state.error_code[0])


        state = init_state.validate({'Connected': False}, False)
        self.assertEqual(len(state.error_code), 2)
        self.assertEqual(StateErrorEnum.CONNECTED_INCONSISTENT_1, state.error_code[0])
        self.assertEqual(StateErrorEnum.CONNECTED_INCONSISTENT_2, state.error_code[1])

    def test_state_discovered_equal(self):
        route='d='
        init_state = State({'Connected': False, 'Discovered': False})
        json_data = {'Connected': False, 'Discovered': False}
        state = init_state.validate(json_data, False)
        self.assertEqual(len(state.error_code), 0)

        init_state = State({'Connected': True, 'Discovered': False})
        state = init_state.validate({'Connected': True, 'Discovered': False}, True)
        self.assertEqual(len(state.error_code), 0)

        init_state = State({'Connected': True, 'Discovered': True})
        state = init_state.validate({'Connected': True, 'Discovered': True}, True)
        self.assertEqual(len(state.error_code), 0)

    def test_state_discovered_not_equal(self):
        init_state = State({'Connected': True, 'Discovered': False})
        state = init_state.validate({'Connected': True, 'Discovered': True}, True)
        self.assertEqual(len(state.error_code), 1)
        self.assertEqual(state.error_code[0], StateErrorEnum.DISCOVERED_INCONSISTENT)

    def test_state_not_connected_and_discovered(self):
        init_state = State({'Connected': False, 'Discovered': True})
        state = init_state.validate({'Connected': False, 'Discovered': True}, False)
        self.assertEqual(len(state.error_code), 1)
        self.assertEqual(state.error_code[0], StateErrorEnum.NOT_CONNECTED)

    def test_translate_error_codes(self):
        state = State({'Errorcode': None, 'Error': None})
        state.translate_error_codes()
        self.assertNotEqual(state.error_code, None)
        self.assertNotEqual(state.error, None)
        self.assertEqual(len(state.error_code), 0)
        self.assertEqual(len(state.error), 0)

        state = State({'Errorcode': [StateErrorEnum.CONNECTED_INCONSISTENT_1, StateErrorEnum.DISCOVERED_INCONSISTENT]})
        state.translate_error_codes()
        self.assertNotEqual(state.error_code, None)
        self.assertEqual(len(state.error_code), 2)
        self.assertEqual(state.error_code[0], StateErrorEnum.CONNECTED_INCONSISTENT_1)
        self.assertEqual(state.error_code[1], StateErrorEnum.DISCOVERED_INCONSISTENT)
        self.assertNotEqual(state.error, None)
        self.assertEqual(len(state.error), 2)
        self.logger.debug(state.error[0])
        self.logger.debug(state.error[1])
        self.assertEqual(state.error[0], StateErrorEnum.CONNECTED_INCONSISTENT_1.value)
        self.assertEqual(state.error[1], StateErrorEnum.DISCOVERED_INCONSISTENT.value)
