# tests/test_mqtt_client.py
from argparse import Namespace
import time
import unittest
from unittest import mock
from unittest.mock import patch

from paho.mqtt.client import MQTTMessage

from ha_mqtt_pi_smbus.device import HADevice, HASensor
from ha_mqtt_pi_smbus.mqtt_client import (
    State,
    MQTTClient,
    MQTT_Publisher_Thread,
)
from ha_mqtt_pi_smbus.environ import DEGREE
from ha_mqtt_pi_smbus.parsing import MQTTConfig

from .mock_data import (
    MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT,
    MOCK_IFCONFIG_WLAN0_DATA,
    MOCK_IFCONFIG_ETH0_DATA,
    MOCKED_OPEN,
)

"""
Note the methods of MQTTClient aren't necessarily order dependent so
so these tests don't run in the normal functional order.
"""


class Temperature(HASensor):
    def __init__(self, name: str):
        super().__init__("%sC" % (DEGREE))


class Humidity(HASensor):
    def __init__(self, name: str):
        super().__init__("%")


class Pressure(HASensor):
    def __init__(self, name: str):
        super().__init__("mbar")


class BME280_Device(HADevice):
    def __init__(self):
        super().__init__(
            (Temperature(), Humidity(), Pressure()),
            "Office",
            "me/state",
            "Bosch",
            "BME280",
        )


class TestMQTTClient(unittest.TestCase):
    def setUp(self):
        self.parser = Namespace(
            logginglevel="DEBUG", title="Test Title", subtitle="Test Subtitle"
        )
        self.mocked_open = MOCKED_OPEN
        self.mocked_open.start()

    def tearDown(self):
        self.mocked_open.stop()

    @patch("paho.mqtt.client.Client.is_connected")
    @patch("paho.mqtt.client.Client.connect")
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_connect_error(
        self, mock_smbus, mock_connect, mock_is_connected
    ):

        mock_connect.return_value = 1
        with patch("builtins.open", self.mocked_open), patch(
            "subprocess.check_output"
        ) as mock_subprocess_check_output:

            mock_subprocess_check_output.side_effect = (
                MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT * 10
            )
            mqtt_client = MQTTClient(
                client_prefix="me",
                device=(),
                smbus_device=mock_smbus,
                mqtt_config=MQTTConfig(
                    broker = "127.0.0.1",
                    port = 1883,
                    username = "me",
                    password = "mine",
                    qos = 1,
                    retain = True,
                ),
            )
            rc = mqtt_client.connect_mqtt()
            assert rc == 1

    @patch("subprocess.check_output")
    @patch("paho.mqtt.client.Client.is_connected")
    @patch("paho.mqtt.client.Client.connect")
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice.getdata")
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_publisher_thread(
        self,
        mock_smbus,
        mock_data,
        mock_connect,
        mock_is_connected,
        mock_subprocess_check_output,
    ):
        with patch("builtins.open", self.mocked_open), patch(
            "subprocess.check_output"
        ) as mock_subprocess_check_output:

            mock_subprocess_check_output.side_effect = (
                MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT * 10
            )
            mock_connect.return_value = 0
            mock_is_connected.return_value = False
            mock_data.side_effect = [{"last_update": i} for i in range(1, 11)]
            mqtt_client = MQTTClient(
                client_prefix="me",
                device=(),
                smbus_device=mock_smbus,
                mqtt_config=MQTTConfig(
                    broker = "127.0.0.1",
                    port = 1883,
                    username = "me",
                    password = "mine",
                    qos = 1,
                    retain = True,
                ),
            )
            thread = MQTT_Publisher_Thread(
                mqtt_client,
                HADevice(
                    [
                        HASensor(
                            DEGREE, name="temperature", device_class="temperature"
                        ),
                        HASensor("mbar", name="pressure", device_class="pressure"),
                        HASensor("%", name="humidity", device_class="humidity"),
                        ],
                    "me",
                    "my/state",
                    "God",
                    "WASP",
                ),
                mock_smbus,
            )
            obj = {
                "Connected": False,
                "Discovered": False,
                "rc": 0,
                "Error": ["Error!"],
            }
            mqtt_client.state = State(obj)
            assert mqtt_client.connect_mqtt() == 0
            assert not mqtt_client.is_connected()
            thread.start()
            assert thread.data["last_update"] == 2
            time.sleep(1.1)
            assert thread.data["last_update"] == 3
            thread.clear_do_run()
            thread.join()

    @patch("subprocess.check_output")
    @patch("paho.mqtt.client.Client.is_connected")
    @patch("paho.mqtt.client.Client.disconnect")
    @patch("paho.mqtt.client.Client.connect")
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_connect_disconnect(
        self,
        mock_smbus,
        mock_connect,
        mock_disconnect,
        mock_is_connected,
        mock_subprocess_check_output,
    ):
        mock_subprocess_check_output.side_effect = [
            MOCK_IFCONFIG_ETH0_DATA.encode("utf-8"),
            MOCK_IFCONFIG_WLAN0_DATA.encode("utf-8"),
        ] * 10
        mock_connect.return_value = 0
        mock_disconnect.side_effect = [0, 1]
        mock_is_connected.return_value = False
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=(),
            smbus_device=mock_smbus,
            mqtt_config=MQTTConfig(
                broker = "127.0.0.1",
                port = 1883,
                username = "me",
                password = "mine",
                qos = 1,
                retain = True,
            ),
        )
        obj = {"Connected": False, "Discovered": False, "rc": 0, "Error": ["Error!"]}
        mqtt_client.state = State(obj)
        assert mqtt_client.connect_mqtt() == 0
        assert not mqtt_client.is_connected()
        assert not mqtt_client.state.connected
        MQTTClient.on_connect(mqtt_client, None, None, 0)
        assert mqtt_client.state.connected
        assert len(mqtt_client.state.error) == 0
        MQTTClient.on_disconnect(mqtt_client, None, None, 0)
        assert not mqtt_client.state.connected
        MQTTClient.on_connect(mqtt_client, None, None, 0)
        assert mqtt_client.state.connected
        assert len(mqtt_client.state.error) == 0
        mqtt_client.disconnect_mqtt()
        MQTTClient.on_disconnect(mqtt_client, None, None, 1)
        assert (
            mqtt_client.state.error[0]
            == "Connection Refused: unacceptable protocol version."
        )
        assert mqtt_client.connect_mqtt() == 0
        assert mqtt_client.disconnect_mqtt() == 1
        assert not mqtt_client.is_discovered()

    @patch("subprocess.check_output")
    @patch("paho.mqtt.client.Client.is_connected")
    @patch("paho.mqtt.client.Client.connect")
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_on_connect_error(
        self, mock_smbus, mock_connect, mock_is_connected, mock_subprocess_check_output
    ):
        mock_subprocess_check_output.side_effect = [
            MOCK_IFCONFIG_ETH0_DATA.encode("utf-8"),
            MOCK_IFCONFIG_WLAN0_DATA.encode("utf-8"),
        ] * 10
        mock_connect.return_value = 0
        mock_is_connected.side_effect = [False] * 20
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=(),
            smbus_device=mock_smbus,
            mqtt_config=MQTTConfig(
                broker = "127.0.0.1",
                port = 1883,
                username = "me",
                password = "mine",
                qos = 1,
                retain = True,
            ),
        )
        obj = {"Connected": False, "Discovered": False, "rc": 1, "Error": ["Error!"]}
        mqtt_client.state = State(obj)
        assert mqtt_client.connect_mqtt() == 0
        assert not mqtt_client.is_connected()
        assert not mqtt_client.state.connected
        MQTTClient.on_connect(mqtt_client, None, None, 1)
        assert not mqtt_client.state.connected
        assert len(mqtt_client.state.error) == 1
        assert (
            mqtt_client.state.error[0]
            == "Connection Refused: unacceptable protocol version."
        )

    @patch("subprocess.check_output")
    @patch("paho.mqtt.client.Client.is_connected")
    @patch("paho.mqtt.client.Client.connect")
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_on_connect(
        self, mock_smbus, mock_connect, mock_is_connected, mock_subprocess_check_output
    ):
        mock_subprocess_check_output.side_effect = [
            MOCK_IFCONFIG_ETH0_DATA.encode("utf-8"),
            MOCK_IFCONFIG_WLAN0_DATA.encode("utf-8"),
        ] * 10
        mock_connect.return_value = 0
        mock_is_connected.side_effect = [False] * 20
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=(),
            smbus_device=mock_smbus,
            mqtt_config=MQTTConfig(
                broker = "127.0.0.1",
                port = 1883,
                username = "me",
                password = "mine",
                qos = 1,
                retain = True,
                ),
        )
        obj = {"Connected": False, "Discovered": False, "rc": 1, "Error": ["Error!"]}
        mqtt_client.state = State(obj)
        assert mqtt_client.connect_mqtt() == 0
        assert not mqtt_client.is_connected()
        assert not mqtt_client.state.connected
        MQTTClient.on_connect(mqtt_client, None, None, 0)
        assert mqtt_client.state.connected

    @patch("subprocess.check_output")
    @patch("paho.mqtt.client.Client.is_connected")
    @patch("paho.mqtt.client.Client.connect")
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_is_connected_error(
        self, mock_smbus, mock_connect, mock_is_connected, mock_subprocess_check_output
    ):
        mock_subprocess_check_output.side_effect = [
            MOCK_IFCONFIG_ETH0_DATA.encode("utf-8"),
            MOCK_IFCONFIG_WLAN0_DATA.encode("utf-8"),
        ] * 10
        mock_connect.return_value = 0
        mock_is_connected.side_effect = [False] * 20
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=(),
            smbus_device=mock_smbus,
            mqtt_config=MQTTConfig(
                broker = "127.0.0.1",
                port = 1883,
                username = "me",
                password = "mine",
                qos = 1,
                retain = True,
            ),
        )
        obj = {"Connected": False, "Discovered": False, "rc": 1, "Error": ["Error!"]}
        mqtt_client.state = State(obj)
        assert mqtt_client.connect_mqtt() == 0
        assert not mqtt_client.is_connected()
        assert not mqtt_client.state.connected
        MQTTClient.on_connect(mqtt_client, None, None, 0)
        assert mqtt_client.state.connected
        mqtt_client.state.connected = True
        assert mqtt_client.is_connected() is None

    @patch("subprocess.check_output")
    @patch("paho.mqtt.client.Client.subscribe")
    @patch("paho.mqtt.client.Client.is_connected")
    @patch("paho.mqtt.client.Client.connect")
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_subscribe(
        self,
        mock_smbus,
        mock_connect,
        mock_is_connected,
        mock_subscribe,
        mock_subprocess_check_output,
    ):
        mock_subprocess_check_output.side_effect = [
            MOCK_IFCONFIG_ETH0_DATA.encode("utf-8"),
            MOCK_IFCONFIG_WLAN0_DATA.encode("utf-8"),
        ] * 10
        mock_connect.return_value = 0
        mock_subscribe.return_value = (0, 1)
        mock_is_connected.side_effect = [False] * 20
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=(),
            smbus_device=mock_smbus,
            mqtt_config=MQTTConfig(
                broker = "127.0.0.1",
                port = 1883,
                username = "me",
                password = "mine",
                qos = 1,
                retain = True,
                ),
        )
        obj = {"Connected": False, "Discovered": False, "rc": 1, "Error": ["Error!"]}
        mqtt_client.state = State(obj)
        assert mqtt_client.connect_mqtt() == 0
        assert not mqtt_client.is_connected()
        assert not mqtt_client.state.connected
        MQTTClient.on_connect(mqtt_client, None, None, 0)
        assert mqtt_client.state.connected
        rc = mqtt_client.subscribe("my/state")
        assert len(rc) == 2

    @patch("builtins.open")
    @patch("subprocess.check_output")
    @patch("paho.mqtt.client.Client.publish")
    @patch("paho.mqtt.client.Client.is_connected")
    @patch("paho.mqtt.client.Client.connect")
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_publish(
        self,
        mock_smbus,
        mock_connect,
        mock_is_connected,
        mock_subscribe,
        mock_subprocess_check_output,
        mock_builtin_open,
    ):
        with patch("builtins.open", self.mocked_open), patch(
            "subprocess.check_output"
        ) as mock_subprocess_check_output:

            mock_subprocess_check_output.side_effect = (
                MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT * 10
            )
            mock_connect.return_value = 0
            mock_subscribe.return_value = (0, 1)
            mock_is_connected.side_effect = [False] * 20
            mqtt_client = MQTTClient(
                client_prefix="me",
                device=HADevice(
                    [
                        HASensor(
                            DEGREE, name="temperature", device_class="temperature"
                        ),
                        HASensor("mbar", name="pressure", device_class="pressure"),
                        HASensor("%", name="humidity", device_class="humidity"),
                        ],
                    "me",
                    "my/state",
                    "God",
                    "WASP",
                ),
                smbus_device=mock_smbus,
                mqtt_config=MQTTConfig(
                    broker = "127.0.0.1",
                    port = 1883,
                    username = "me",
                    password = "mine",
                    qos = 1,
                    retain = True,
                    ),
            )
            obj = {
                "Connected": False,
                "Discovered": False,
                "rc": 1,
                "Error": ["Error!"],
            }
            mqtt_client.state = State(obj)
            assert mqtt_client.connect_mqtt() == 0
            assert not mqtt_client.is_connected()
            assert not mqtt_client.state.connected
            MQTTClient.on_connect(mqtt_client, None, None, 0)
            assert mqtt_client.state.connected
            rc = mqtt_client.subscribe("my/state")
            assert len(rc) == 2
            mqtt_client.publish_discovery(mqtt_client.device)
            mqtt_client.publish_available(mqtt_client.device)
            mqtt_client.clear_discovery(mqtt_client.device)

    @patch('ha_mqtt_pi_smbus.environ.getMacAddress', return_value='12:34:56')
    @patch('ha_mqtt_pi_smbus.environ.getObjectId', return_value='123456')
    @patch('ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_available')
    @patch('ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_discovery')
    def test_on_message_online(self, mock_discovery, mock_available, mock_object_id, mock_mac_address):
        config = MQTTConfig()
        client = MQTTClient(None, None, None, config)
        client.is_discovered = True
        msg = MQTTMessage(topic=client.status_topic.encode('utf-8'))
        msg.payload = b'online'
        client.on_message(None, None, msg)
        mock_discovery.assert_called_once()
        mock_available.assert_called_once()

    @patch('ha_mqtt_pi_smbus.environ.getMacAddress', return_value='12:34:56')
    @patch('ha_mqtt_pi_smbus.environ.getObjectId', return_value='123456')
    @patch('ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_available')
    @patch('ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_discovery')
    def test_on_message_offline(self, mock_discovery, mock_available, mock_object_id, mock_mac_address):
        config = MQTTConfig()
        client = MQTTClient(None, None, None, config)
        client.is_discovered = True
        msg = MQTTMessage(topic=client.status_topic.encode('utf-8'))
        msg.payload = b'offline'
        client.on_message(None, None, msg)
        self.assertFalse(client.is_discovered)

    @patch('ha_mqtt_pi_smbus.environ.getMacAddress', return_value='12:34:56')
    @patch('ha_mqtt_pi_smbus.environ.getObjectId', return_value='123456')
    @patch('ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_available')
    @patch('ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_discovery')
    def test_on_message_bad(self, mock_discovery, mock_available, mock_object_id, mock_mac_address):
        config = MQTTConfig()
        client = MQTTClient(None, None, None, config)
        client.is_discovered = True
        msg = MQTTMessage(topic=client.status_topic.encode('utf-8'))
        msg.payload = b'bad'
        client.on_message(None, None, msg)
        self.assertTrue(client.is_discovered)
        mock_discovery.assert_not_called()
        mock_available.assert_not_called()

    @patch('ha_mqtt_pi_smbus.environ.getMacAddress', return_value='12:34:56')
    @patch('ha_mqtt_pi_smbus.environ.getObjectId', return_value='123456')
    @patch('ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_available')
    @patch('ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_discovery')
    def test_on_message_badtopic(self, mock_discovery, mock_available, mock_object_id, mock_mac_address):
        config = MQTTConfig()
        client = MQTTClient(None, None, None, config)
        client.is_discovered = True
        msg = MQTTMessage(topic=b'bad')
        msg.payload = b'bad'
        client.on_message(None, None, msg)
        self.assertTrue(client.is_discovered)
        mock_discovery.assert_not_called()
        mock_available.assert_not_called()
























