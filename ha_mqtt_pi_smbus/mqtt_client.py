from __future__ import annotations

import copy
from importlib.metadata import version, PackageNotFoundError
import json
import logging
import random
import threading
import time
from typing import Any, Dict

import paho.mqtt.client as mqtt
import paho.mqtt.enums as mqtt_enums
import paho.mqtt.properties as mqtt_properties
from paho.mqtt.client import connack_string

from ha_mqtt_pi_smbus.device import HADevice, HASensor, SMBusDevice
from ha_mqtt_pi_smbus.environ import (
    getObjectId,
    getTemperature,
    getUptime,
    getLastRestart,
)
from ha_mqtt_pi_smbus.parsing import MQTTConfig
from ha_mqtt_pi_smbus.state import State


def getTemp():
    return getTemperature()


class MQTT_Publisher_Thread(threading.Thread):
    """
    A class used to represent a thread which, at intervals, publishes
    data to Home Assistant through MQTT

    Attributes
    ----------
    client : MQTTClient
        a MQTTClient instance which is used to publish data
    device : HADevice
        a HADevice describing the data to be published
    smbus_device : SMBusDevice
        the representation of the physical device whose data is to
        be published
    __logger : logging:Logger
        the logger instance used to send messages to the logs
    do_run : bool
        the execution flag, initialized to True. when it changes to
        False, the run() processor will exit at the beginning of the
        next iteration
    data : Any
        the data which will be encoded and sent to Home Assistant

    Methods
    -------
    run()
        The main thread execution method
    clear_do_run()
        clears the run() methods execution flag causing the run() method
        to exit at the beginning of the next iteration.


    """

    def __init__(
        self, client: "MQTTClient", device: HADevice, smbus_device: SMBusDevice
    ):
        """
        Parameters
        ----------
        client : MQTTClient
            the client used to communicate with the MQTT broker
        device : HADevice
            the description of the data to be sent to Home Assistant
            through the MQTT broker
        smbus_device : SMBusDevice
            the device which contains the data to be sent
        """
        super().__init__(name="MQTT_Publisher", daemon=True)
        self.client = client
        self.device = device
        self.smbus_device = smbus_device
        self.__logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.do_run = True
        self.data = self.smbus_device.getdata()

    def run(self) -> None:
        """the main execution method for the thread

        Parameters
        ----------
        None
        """
        while True:
            if not self.do_run:
                return
            if self.client.is_discovered:
                data = copy.deepcopy(self.smbus_device.getdata())
                if data["last_update"] != self.data["last_update"]:
                    self.data = copy.deepcopy(data)
                    self.data["state"] = "OK"
                    self.client.publish(
                        self.device.state_topic,
                        json.dumps(self.data),
                        qos=self.client.qos,
                        retain=self.client.retain,
                    )
            time.sleep(1)

    def clear_do_run(self) -> None:
        """the run() routine's do_run flag is cleared

        Parameters
        ----------
        None
        """
        self.do_run = False


class MQTTClient(mqtt.Client):
    """a class extending the paho MQTT client

    Attributes
    ----------
    state : State
        a dict containing 3 items:
            connected:bool which indicates the connection state of the
            client
            rc : int the return code of the MQTT client
            error : str the error message sent to the web page
    broker_address : str
        the host name or IP-address of the MQTT broker
    port : int
        the port number which is used to connect with the MQTT broker
    username : str
        the username used to authenticate with the MQTT broker
    password : str
        the password used to authenticate with the MQTT broker
    device : HADevice
        the description of the data being sent to Home Assitant through
        the MQTT broker
    smbus_device : SMBusDevice
        the interface to the sensor device
    connected : bool
    connected_flag : bool
    on_connect : Callback
        the method which will be called when a connection is complete
    publisher_thread : MQTT_Publisher_Thread
        the thread which will retrieve data from the smbus_device and
        publish it via the MQTT client
    __logger : logging.Logger
        the logger instance used to log messages
    """

    def on_connect(client, userdata, flags, rc, properties=None) -> None:
        """Callback function called when the client connects to the broker."""
        client.state.rc = rc
        if rc == 0:
            client.state.connected = True
            client.__logger.info("Connected to MQTT broker")
            client.subscribe(client.status_topic)
            client.__logger.debug(
                f"Subscribed to HA status topic: {client.status_topic}"
            )

        else:
            client.state.error = [connack_string(rc)]

    def on_disconnect(client, userdata, flags, rc, Properties=None) -> None:
        if rc == 0:
            # client.close()
            client.state.connected = False
        else:
            client.state.error = [connack_string(rc)]

    def on_message(client, userdata, xxx, msg) -> None:
        payload = msg.payload.decode("utf-8").strip().lower()
        if msg.topic == client.status_topic:
            if payload == "online":
                client.__logger.info("Home Assistant is ONLINE")
                client.publish_discovery(client.device)
                client.publish_available(client.device)
            elif payload == "offline":
                client.__logger.warning("Home Assistant is OFFLINE")
                client.is_discovered = False
            else:
                client.__logger.debug(f"HA status unknown payload: {payload}")
        else:
            client.__logger.debug(f"message unknown topic: {msg.topic}")

    def __init__(
        self,
        client_prefix: str,
        device: HADevice,
        smbus_device: SMBusDevice,
        mqtt_config: MQTTConfig = None,
    ):
        """
        Paameters
        ---------
        client_prefix : str
            a name prefix which is used to build a unique connection to
            MQTT
        device : HADevice
            the device containing the description of the data to be sent
            to MQTT
        smbus_device : SMBusDevice
            the physical device instance from which data is obtained
        mqtt_config : MQTT
            configuration data provided to the client:
            broker : str
                host name or IP-address of the MQTT broker
            port : int
                the broker port number
            username : str
                the username used to authenticate to the MQTT broker
            password : str
                the password used to authenticate to the MQTT broker
            qos: int
                the quality of service to be used with the MQTT broker
            retain: bool
                the retain policy to be used with the MQTT broker
        """
        super().__init__(
            mqtt_enums.CallbackAPIVersion.VERSION2,
            f"{client_prefix}-{getObjectId()}-{str(random.randint(0,1000)).zfill(3)}",
            True,
            None,
        )
        self.broker_address = mqtt_config.broker
        self.port = mqtt_config.port
        self.username = mqtt_config.username
        self.password = mqtt_config.password
        self.qos = mqtt_config.qos
        self.retain = mqtt_config.retain
        self.status_topic = mqtt_config.status_topic
        self.device = device
        self.smbus_device = smbus_device
        self.state = State()
        self.connected = False
        self.connected_flag = False
        self.on_connect = MQTTClient.on_connect
        self.on_disconnect = MQTTClient.on_disconnect
        self.on_messagee = MQTTClient.on_message
        self.publisher_thread = None
        super().user_data_set(self)
        self.__logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

    def connect_mqtt(self) -> int:
        """Initiate a connection to the MQTT broker"""
        route = "connect_mqtt"
        super().username_pw_set(self.username, self.password)
        self.state = State()
        self.__logger.info(
            "%s connecting to broker at %s:%s", route, self.broker_address, self.port
        )
        mqttErrorCode = super().connect(self.broker_address, self.port)
        if mqttErrorCode != 0:
            self.__logger.critical("%s error %s in connect_mqtt", route, mqttErrorCode)
        return mqttErrorCode

    def is_connected(self) -> bool | None:
        connected = super().is_connected()
        if connected == self.state.connected:
            return connected
        return None

    def disconnect_mqtt(self) -> int:
        """disconnect from the MQTT broker"""
        route = "disconnect_mqtt"
        mqttErrorCode = super().disconnect()
        if mqttErrorCode != 0:
            self.__logger.critical(
                "%s error %s in disconnect_mqtt", route, mqttErrorCode
            )
        return mqttErrorCode

    def is_discovered(self) -> bool:
        return self.state.discovered

    def subscribe(self, topic: str) -> None:
        """subscribe to messages from the MQTT broker

        The client is subscribed to the topic supplied
        """
        route = "subscribe"
        self.__logger.info('%s subscribing to topic "%s"', route, topic)
        tuple = super().subscribe(topic)
        return tuple

    def publish(
        self,
        topic: str,
        message: str,
        qos: int = None,
        retain: bool = True,
        properties: mqtt_properties.Properties | None = None,
    ):
        """publish a messge to Home Assistant via the MQTT broker

        Parameters
        ----------
        topic : str
            the topic which is used to send the message, it might be
            either a state topic, or a discovery topic
        message : str
            the message which is to be sent. This will normally a
            json-encoded dict containing state data, discovery data,
            or a zero-length un-discovery message
        qos : int
            0 - only once - "fire and forget"
            1 - at least once
            2 - exactly once
        retain : bool
            retain the message in the MQTT broker
        properties : paho.mqtt.properties.Properties
            A set of properties for the message, if desired
        """
        route = "publish"
        self.__logger.info(
            "%s publishing to Topic = %s, Payload = %s, "
            + "QOS = %s, Retain = %s, Properties = %s",
            route,
            topic,
            message,
            qos,
            retain,
            properties,
        )
        result = super().publish(topic, message, qos, retain, properties)
        status = result[0]
        mid = result[1]
        if status != 0:
            self.__logger.error(
                "%s Failed to send message to topic %s, rc %s, mid %s",
                route,
                topic,
                status,
                mid,
            )
        return result

    def publish_discovery(self, device: HADevice) -> None:
        """Publish a discovery message for each sensor in the device

        Parameters
        ----------
        sensors : Dict[str, Any]
            a set of sensor_name, sensor pairs

        """
        self.device = device
        self.publish(
            self.device.discovery_topic,
            json.dumps(device.discovery_payload),
            qos=self.qos,
            retain=self.retain,
        )
        self.publisher_thread = MQTT_Publisher_Thread(
            self, self.device, self.smbus_device
        )
        self.publisher_thread.start()
        self.state.discovered = True

    def publish_available(self, device: HADevice | HASensor) -> None:
        """Publish an available message for the given sensor or each sensor
        in the device

        Parameters
        ----------
        device : HADevice | HASensor
            a device or sensor

        """
        if isinstance(device, HADevice):
            for sensor in device.sensors:
                self.publish_available(sensor)
            return
        if not isinstance(device, HASensor):
            raise Exception(
                f"device ({self.__class__.__module__}.{self.__class__.__name__}) must be an instance of HADevice or HASensor"
            )  # pragma: no cover
        sensor = device
        if sensor.diagnostic:
            try:
                __version__ = version("ha_mqtt_pi_smbus")
            except PackageNotFoundError:
                __version__ = "0.0.0"
            temperature = getTemperature()
            logging.getLogger(__name__).error("temperature: %d", temperature)
            sensor.diagnosticData = {
                "status": "OK",
                "cpu_temperature": temperature,
                "version": __version__,
                "uptime": getUptime(),
                "last_restart": getLastRestart(),
            }
            self.publish(
                sensor.discovery_payload["json_attributes_topic"],
                json.dumps(sensor.diagnosticData),
                qos=self.qos,
                retain=self.retain,
            )
        else:
            self.publish(
                sensor.availability.topic,
                json.dumps({"availability": sensor.availability.payload_available}),
                qos=self.qos,
                retain=self.retain,
            )

    def publish_not_available(self, device: HADevice | HASensor) -> None:
        """Publish an unvailable message for the sensor or each sensor
        in the device

        Parameters
        ----------
        device : HADevice | HASensor
            a device or a sensor

        """
        if isinstance(device, HADevice):
            for sensor in device.sensors:
                self.publish_not_available(sensor)
            return
        if not isinstance(device, HASensor):
            raise Exception(
                f"device ({self.__class__.__module__}.{self.__class__.__name__} must be an instance of HADevice or HASensor"
            )  # pragma: no cover
        sensor = device
        self.publish(
            sensor.availability.topic,
            json.dumps({"availability": sensor.availability.payload_not_available}),
            qos=self.qos,
            retain=self.retain,
        )

    def clear_discovery(self, device: HADevice) -> None:
        """Publish a clear discovery message for each sensor in the device

        Parameters
        ----------
        sensors : Dict[str, Any]
            a set of sensor_name, sensor pairs

        """
        self.publish_not_available(device)
        self.publish(
            device.discovery_topic,
            json.dumps(device.undiscovery_payload1),
            qos=self.qos,
            retain=self.retain,
        )
        self.state.discovered = False
        self.publisher_thread.clear_do_run()
        self.publisher_thread.join()
        self.publisher_thread = None
