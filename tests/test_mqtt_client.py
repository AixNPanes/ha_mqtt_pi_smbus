# tests/test_mqtt_client.py
import logging
import pytest
import time
from unittest import TestCase
from unittest.mock import patch, MagicMock

from paho.mqtt.client import MQTTMessage,MQTTErrorCode

from ha_mqtt_pi_smbus.device import HADevice, HASensor
from ha_mqtt_pi_smbus.mqtt_client import (
    State,
    MQTTClient,
    MQTT_Publisher_Thread,
    getTemp,
)
from ha_mqtt_pi_smbus.environ import DEGREE
from ha_mqtt_pi_smbus.mqtt_client import getTemp
from ha_mqtt_pi_smbus.config import Config,MqttConfig

from .mock_data import (
    MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT,
    MOCK_IFCONFIG_WLAN0_DATA,
    MOCK_IFCONFIG_ETH0_DATA,
    MOCK_CPUINFO_DATA,
    MOCK_CONFIG_DATA,
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
            [Temperature("test"), Humidity("test"), Pressure("test")],
            "Office",
            "me/state",
            "Bosch",
            "BME280",
        )


class TestMQTTClient(TestCase):
    def setUp(self):
        self.config = Config({
            'web': {
                'broker':"127.0.0.1",
                'port':1883,
                'username':"me",
                'password':"mine",
                'qos':1,
                'retain':True,
                },
            'mqtt':{}
            })

    @patch("ha_mqtt_pi_smbus.device.getObjectId", return_value="0123456789abcdef")
    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch(
        "ha_mqtt_pi_smbus.environ.get_command_data",
        side_effect=[MOCK_IFCONFIG_WLAN0_DATA],
    )
    @patch("paho.mqtt.client.Client.is_connected")
    @patch("paho.mqtt.client.Client.connect", return_value=1)
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_connect_error(
        self,
        mock_smbus,
        mock_connect,
        mock_is_connected,
        mock_command,
        mock_cpuinfo,
        mock_objecid,
    ):
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=(BME280_Device()),
            smbus_device=mock_smbus,
            config=self.config
        )
        rc = mqtt_client.connect_mqtt()
        assert rc == 1

    @patch("ha_mqtt_pi_smbus.device.getObjectId", return_value="0123456789abcdef")
    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch(
        "ha_mqtt_pi_smbus.environ.get_command_data",
        side_effect=[MOCK_IFCONFIG_WLAN0_DATA],
    )
    @patch("paho.mqtt.client.Client.is_connected", side_effect=[False] * 20)
    @patch("paho.mqtt.client.Client.connect", return_value=0)
    @patch(
        "ha_mqtt_pi_smbus.device.SMBusDevice.getdata",
        side_effect=[{"last_update": i} for i in range(1, 11)],
    )
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice", return_value=(1, 0x76))
    def test_mqtt_client_publisher_thread(
        self,
        mock_smbus,
        mock_data,
        mock_connect,
        mock_is_connected,
        mock_subprocess_check_output,
        mock_read,
        mock_object_id,
    ):
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=(BME280_Device()),
            smbus_device=mock_smbus,
            config=self.config,
        )
        thread = MQTT_Publisher_Thread(
            mqtt_client,
            HADevice(
                [
                    HASensor(DEGREE, name="temperature", device_class="temperature"),
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

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch("subprocess.check_output", side_effect = [
            MOCK_IFCONFIG_ETH0_DATA.encode("utf-8"),
            MOCK_IFCONFIG_WLAN0_DATA.encode("utf-8"),
        ] * 10)
    @patch("paho.mqtt.client.Client.is_connected", return_value=False)
    @patch("paho.mqtt.client.Client.disconnect", side_effect=[1, 1])
    @patch("paho.mqtt.client.Client.connect", return_value = 0)
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_connect_disconnect(
        self,
        mock_smbus,
        mock_connect,
        mock_disconnect,
        mock_is_connected,
        mock_subprocess_check_output,
        mock_readfile,
    ):
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=(BME280_Device()),
            smbus_device=mock_smbus,
            config=self.config,
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

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch(
        "subprocess.check_output",
        side_effect=[
            MOCK_IFCONFIG_ETH0_DATA.encode("utf-8"),
            MOCK_IFCONFIG_WLAN0_DATA.encode("utf-8"),
        ]
        * 10,
    )
    @patch("paho.mqtt.client.Client.is_connected", side_effect=[False] * 20)
    @patch("paho.mqtt.client.Client.connect", return_value=0)
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_on_connect_error(
        self,
        mock_smbus,
        mock_connect,
        mock_is_connected,
        mock_subprocess_check_output,
        mock_cpuinfo,
    ):
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=(BME280_Device()),
            smbus_device=mock_smbus,
            config=self.config,
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

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch(
        "subprocess.check_output",
        side_effect=[
            MOCK_IFCONFIG_ETH0_DATA.encode("utf-8"),
            MOCK_IFCONFIG_WLAN0_DATA.encode("utf-8"),
        ]
        * 10,
    )
    @patch("paho.mqtt.client.Client.is_connected", side_effect=[False] * 20)
    @patch("paho.mqtt.client.Client.connect", return_value=0)
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_on_connect(
        self,
        mock_smbus,
        mock_connect,
        mock_is_connected,
        mock_subprocess_check_output,
        mock_cpuinfo,
    ):
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=(BME280_Device()),
            smbus_device=mock_smbus,
            config=self.config,
        )
        obj = {"Connected": False, "Discovered": False, "rc": 1, "Error": ["Error!"]}
        mqtt_client.state = State(obj)
        assert mqtt_client.connect_mqtt() == 0
        assert not mqtt_client.is_connected()
        assert not mqtt_client.state.connected
        MQTTClient.on_connect(mqtt_client, None, None, 0)
        assert mqtt_client.state.connected

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch(
        "subprocess.check_output",
        side_effect=[
            MOCK_IFCONFIG_ETH0_DATA.encode("utf-8"),
            MOCK_IFCONFIG_WLAN0_DATA.encode("utf-8"),
        ]
        * 10,
    )
    @patch("paho.mqtt.client.Client.is_connected", return_value=0)
    @patch("paho.mqtt.client.Client.connect", side_effect=[False] * 20)
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_is_connected_error(
        self,
        mock_smbus,
        mock_connect,
        mock_is_connected,
        mock_subprocess_check_output,
        mock_cpuinfo,
    ):
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=(BME280_Device()),
            smbus_device=mock_smbus,
            config=self.config,
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

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch(
        "subprocess.check_output",
        side_effect=[
            MOCK_IFCONFIG_ETH0_DATA.encode("utf-8"),
            MOCK_IFCONFIG_WLAN0_DATA.encode("utf-8"),
        ]
        * 10,
    )
    @patch("paho.mqtt.client.Client.subscribe", return_value=(0, 1))
    @patch("paho.mqtt.client.Client.is_connected", side_effect=[False] * 20)
    @patch("paho.mqtt.client.Client.connect", return_value=0)
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice")
    def test_mqtt_client_subscribe(
        self,
        mock_smbus,
        mock_connect,
        mock_is_connected,
        mock_subscribe,
        mock_subprocess_check_output,
        mock_cpuinfo,
    ):
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=(BME280_Device()),
            smbus_device=mock_smbus,
            config=self.config,
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

    @patch("ha_mqtt_pi_smbus.mqtt_client.getTemperature", return_value=30000)
    @patch(
        "ha_mqtt_pi_smbus.mqtt_client.getUptime",
        return_value="up 1 week, 11 hours, 13 minutes",
    )
    @patch("ha_mqtt_pi_smbus.environ.readfile", side_effect=[MOCK_CPUINFO_DATA])
    @patch(
        "ha_mqtt_pi_smbus.environ.get_command_data",
        side_effect=[MOCK_IFCONFIG_WLAN0_DATA] * 10,
    )
    @patch("paho.mqtt.client.Client.publish", return_value=(0, 1))
    @patch("paho.mqtt.client.Client.is_connected", side_effect=[False] * 20)
    @patch("paho.mqtt.client.Client.connect", return_value=0)
    @patch("ha_mqtt_pi_smbus.device.SMBusDevice", return_value=(1, 0x76))
    def test_mqtt_client_publish_ok(
        self,
        mock_smbus,
        mock_connect,
        mock_is_connected,
        mock_subscribe,
        mock_subprocess_check_output,
        mock_builtin_open,
        mock_uptime,
        mock_temperature,
    ):
        sensor1 = HASensor(DEGREE, name="temperature", device_class="temperature")
        sensor2 = HASensor("mbar", name="pressure", device_class="pressure")
        sensor3 = HASensor("%", name="humidity", device_class="humidity")
        device = HADevice(
            [
                sensor1,
                sensor2,
                sensor3,
            ],
            "me",
            "my/state",
            "God",
            "WASP",
        )
        mqtt_client = MQTTClient(
            client_prefix="me",
            device=device,
            smbus_device=mock_smbus,
            config=self.config,
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

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch("ha_mqtt_pi_smbus.environ.getMacAddress", return_value="12:34:56")
    @patch("ha_mqtt_pi_smbus.environ.getObjectId", return_value="123456")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_available")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_discovery")
    def test_on_message_online(
        self,
        mock_discovery,
        mock_available,
        mock_object_id,
        mock_mac_address,
        mock_cpuinfo,
    ):
        client = MQTTClient(None, BME280_Device(), None, self.config)
        client.is_discovered = True
        msg = MQTTMessage(topic=client.status_topic.encode("utf-8"))
        msg.payload = b"online"
        client.on_message(None, None, msg)
        mock_discovery.assert_called_once()
        mock_available.assert_called_once()

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch("ha_mqtt_pi_smbus.environ.getMacAddress", return_value="12:34:56")
    @patch("ha_mqtt_pi_smbus.environ.getObjectId", return_value="123456")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_available")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_discovery")
    def test_on_message_offline(
        self,
        mock_discovery,
        mock_available,
        mock_object_id,
        mock_mac_address,
        mock_cpuinfo,
    ):
        client = MQTTClient(None, BME280_Device(), None, self.config)
        client.is_discovered = True
        msg = MQTTMessage(topic=client.status_topic.encode("utf-8"))
        msg.payload = b"offline"
        client.on_message(None, None, msg)
        self.assertFalse(client.is_discovered)

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch("ha_mqtt_pi_smbus.environ.getMacAddress", return_value="12:34:56")
    @patch("ha_mqtt_pi_smbus.environ.getObjectId", return_value="123456")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_config")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_available")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_discovery")
    def test_on_message_config_topic(
        self,
        mock_discovery,
        mock_available,
        mock_config,
        mock_object_id,
        mock_mac_address,
        mock_cpuinfo,
    ):
        client = MQTTClient(None, BME280_Device(), None, self.config)
        client.is_discovered = True
        msg = MQTTMessage(topic=f'{client.config_topic}/get'.encode("utf-8"))
        msg.payload = b"anye"
        client.on_message(None, None, msg)
        mock_config.assert_called_once()

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch("ha_mqtt_pi_smbus.environ.getMacAddress", return_value="12:34:56")
    @patch("ha_mqtt_pi_smbus.environ.getObjectId", return_value="123456")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_available")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_discovery")
    def test_on_message_bad(
        self,
        mock_discovery,
        mock_available,
        mock_object_id,
        mock_mac_address,
        mock_cpuinfo,
    ):
        client = MQTTClient(None, BME280_Device(), None, self.config)
        client.is_discovered = True
        msg = MQTTMessage(topic=client.status_topic.encode("utf-8"))
        msg.payload = b"bad"
        client.on_message(None, None, msg)
        self.assertTrue(client.is_discovered)
        mock_discovery.assert_not_called()
        mock_available.assert_not_called()

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch("ha_mqtt_pi_smbus.environ.getMacAddress", return_value="12:34:56")
    @patch("ha_mqtt_pi_smbus.environ.getObjectId", return_value="123456")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_available")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_discovery")
    def test_on_message_badtopic(
        self,
        mock_discovery,
        mock_available,
        mock_object_id,
        mock_mac_address,
        mock_cpuinfo,
    ):
        client = MQTTClient(None, BME280_Device(), None, self.config)
        client.is_discovered = True
        msg = MQTTMessage(topic=b"bad")
        msg.payload = b"bad"
        client.on_message(None, None, msg)
        self.assertTrue(client.is_discovered)
        mock_discovery.assert_not_called()
        mock_available.assert_not_called()

    @patch('ha_mqtt_pi_smbus.mqtt_client.getTemperature', return_value=101)
    def test_temp(self, mock_temperature):
        temp = getTemp()
        self.assertEqual(temp, 101)

    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch("ha_mqtt_pi_smbus.environ.getMacAddress", return_value="12:34:56")
    @patch("ha_mqtt_pi_smbus.environ.getObjectId", return_value="123456")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_available")
    @patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_discovery")
    def test_mqtt_parser_none(
        self,
        mock_discovery,
        mock_available,
        mock_object_id,
        mock_mac_address,
        mock_cpuinfo,
    ):
        with pytest.raises(Exception):
            client = MQTTClient(None, BME280_Device(), None, None)

    #@patch("ha_mqtt_pi_smbus.environ.getMacAddress", return_value="12:34:56")
    #@patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_available")
    #@patch("ha_mqtt_pi_smbus.mqtt_client.MQTTClient.publish_discovery")
    @patch("ha_mqtt_pi_smbus.environ.readfile", return_value=MOCK_CPUINFO_DATA)
    @patch("ha_mqtt_pi_smbus.device.getObjectId", return_value="123456")
    @patch("ha_mqtt_pi_smbus.mqtt_client.getObjectId", return_value="123456")
    def test_mqtt_client_publish_config(
        self,
        mock_object_id,
        mock_object_id2,
        mock_cpuinfo,
        #mock_discovery,
        #mock_available,
        #mock_mac_address,
    ):
        device = BME280_Device()
        client = MQTTClient(None, device, None, self.config)
        result = client.publish_config(device)
        self.assertEqual(result[0], MQTTErrorCode.MQTT_ERR_NO_CONN)
