# tests/test_test.py
from unittest import TestCase
from unittest.mock import patch

class TestTest(TestCase):
    def test_test(self):
        with open('/dev/null', 'r') as f \
                , patch('ha_mqtt_pi_smbus.device.getOSInfo') as mock_getOSInfo \
                :
            pass