from __future__ import annotations

import json
import logging
import random
import threading
import time
import traceback
from typing import Any, Dict

import paho.mqtt.client as mqtt
import paho.mqtt.enums as mqtt_enums
import paho.mqtt.properties as mqtt_properties
from paho.mqtt.reasoncodes import ReasonCode

from device import HADevice, SMBusDevice
from environ import getObjectId

class State:
    """ A class used to cotain the state of the MQTT client

    Attributes
    ----------
    connected:bool
        a boolean indicating whether the client is connected to the MQTT broker
    discovered:bool
        a boolean indicting whether the device sensors are in a discovered state
    rc:int
        the return code from the MQTT client
    error:List[str]
        the list of error messages
    """
    connected:bool = False
    discovered:bool = False
    rc:Any = None
    error:str = []

    def __init__(self, obj:dict = None):
        self.__logger = logging.getLogger(__name__+'.'+self.__class__.__name__)
        if obj is None:
            return
        if 'Connected' in obj:
            self.connected = obj['Connected']
        if 'Discovered' in obj:
            self.discovered = obj['Discovered']
        if 'rc' in obj:
            self.rc = obj['rc']
        if 'Error' in obj:
            self.error = obj['Error']

    def to_dict(self):
        if not isinstance(self.error, list):
            self.__logger.exception('self.error is str (%s)' % (type(self.error)))
        if self.rc is not None and  not isinstance(self.rc, ReasonCode):
            self.__logger.exception('self.rc not ReasonCode (%s)' % (type(self.rc)))
            self.__logger.exception('self.rc (%s)' % (self.rc))
        return {
            "Connected": self.connected,
            "Discovered": self.discovered,
            "rc": self.rc.json() if isinstance(self.rc, ReasonCode) else self.rc,
            "Error": self.error}

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
    def __init__(self, client:"MQTTClient", device: HADevice, smbus_device:SMBusDevice):
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
        super().__init__(name='MQTT_Publisher', daemon=True)
        self.client = client
        self.device = device
        self.smbus_device = smbus_device
        self.__logger = logging.getLogger(__name__+'.'+self.__class__.__name__)
        self.do_run = True
        self.data = self.smbus_device.data()

    def run(self) -> None:
        """ the main execution method for the thread

        Parameters
        ----------
        None
        """
        while True:
            if not self.do_run:
                return
            data = self.smbus_device.data()
            if data['last_update'] != self.data['last_update']:
                self.data = data
                self.client.publish(self.device.state_topic, json.dumps(data))
                self.__logger.debug('MQTT publisher: %s', json.dumps(data, indent=4))
            time.sleep(1)

    def clear_do_run(self) -> None:
        """ the run() routine's do_run flag is cleared

        Parameters
        ----------
        None
        """
        self.do_run = False

class MQTTClient(mqtt.Client):
    """ a class extending the paho MQTT client

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
        else:
            client.state.error = [connack_string(rc)]

    def on_disconnect(client, userdata, flabs, rc, Properties=None) -> None:
        if rc == 0:
            # client.close()
            client.state.connected = False
        else:
            client.state.error = [rc]

    def is_discovered(self) -> bool:
        return self.state.discovered

    def __init__(self, client_prefix:str, device:HADevice, smbus_device:SMBusDevice, mqtt_config:Dict[str, Any] = None):
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
        mqtt_config : Dict[str, Any]
            configuration data provided to the client:
            broker : str
                host name or IP-address of the MQTT broker
            port : int
                the broker port number
            username : str
                the username used to authenticate to the MQTT broker
            password : str
                the password used to authenticate to the MQTT broker
        """
        super().__init__(
                mqtt_enums.CallbackAPIVersion.VERSION2, 
                f'{client_prefix}-{getObjectId()}-{str(random.randint(0,1000)).zfill(3)}',
                True, None)
        route = '__init__'
        self.broker_address = mqtt_config['broker']
        self.port = mqtt_config['port']
        self.username = mqtt_config['username']
        self.password = mqtt_config['password']
        self.device = device
        self.smbus_device = smbus_device
        self.state = State()
        self.connected = False
        self.connected_flag = False
        self.on_connect = MQTTClient.on_connect
        self.on_disconnect = MQTTClient.on_disconnect
        self.publisher_thread = None
        super().user_data_set(self)
        self.__logger = logging.getLogger(__name__+'.'+self.__class__.__name__)
        self.__logger.error('%s self: %s', route, self)
        self.__logger.debug('%s self.publisher_thread: %s', route, json.dumps(self.publisher_thread))

    def connect_mqtt(self) -> None:
        """ Initiate a connection to the MQTT broker"""
        route = "connect_mqtt"
        super().username_pw_set(self.username, self.password)
        self.state = State()
        mqttErrorCode = super().connect(self.broker_address, self.port)
        if mqttErrorCode != 0:
            self.__logger.critical('%s error %s in connect_mqtt', route, mqttErrorCode)
        self.__logger.info('%s connecting to broker at %s:%s', route, self.broker_address, self.port)

    def is_connected(self) -> bool | None:
        connected = super().is_connected()
        if (connected == self.state.connected):
            return connected
        return None

    def disconnect_mqtt(self) -> None:
        """ disconnect from the MQTT broker """
        route = "disconnect_mqtt"
        mqttErrorCode = super().disconnect()
        if mqttErrorCode != 0:
            self.__logger.critical('%s error %s in disconnect_mqtt', route, mqttErrorCode)

    def subscribe(self, topici:str) -> None:
        """ subscribe to messages from the MQTT broker

        The client is subscribed to the topic supplied
        """
        route = "subscribe"
        self.__logger.info('%s subscribing to topic "%s"', route, topic)
        tuple = super().subscribe(topic)
        return tuple

    def publish(self, topic:str, message:str, qos: int = 0, retain: bool = False,
                properties: mqtt_properties.Properties | None = None):
        """ publish a messge to Home Assistant via the MQTT broker

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
        self.__logger.info('%s publishing to topic: "%s"', route, topic)
        self.__logger.debug('%s \tmessage: "%s"', route, message)
        result = super().publish(topic, message)
        status = result[0]
        mid = result[1]
        if status == 0:
            self.__logger.debug('%s Sent "%s" to "%s" with mid: %s', route, message, topic, mid)
            pass
        else:
            self.__logger.error('%s Failed to send message to topic %s, rc %s', route, topic, status)
            pass
        return result

    def publish_discovery(self, key:str, sensor:HASensor) -> None:
        """ publish a discovery message

        Parameters
        ----------
        key : str
            the name of the sensor for which discovery is being
            performed
        sensor : HASensor
            the sensor for which discovery is to be initiated
        """
        route = "publish_discovery"
        self.publish(
                sensor.discovery_topic, 
                json.dumps(sensor.discovery_payload), 
                qos=2, retain=True)
        self.__logger.info('%s Published discovery for %s', route, key)

    def clear_discovery(self, key:str, sensor:HASensor) -> None:
        """ publish a clear discovery message for a sensor

        Parameters
        ----------
        key : str
            the name of the sensor for which discovery is being
            cleared
        sensor : HASensor
            the sensor for which discovery is to be cleared
        """
        route = "clear_discovery"
        self.publish(sensor.discovery_topic, "", qos=2, retain=True)
        self.__logger.info('%s Cleared discovery for %s', route, key)

    def publish_discoveries(self, sensors:Dict[str, Any]) -> None:
        """ Publish a discovery message for each sensor in the device

        Parameters
        ----------
        sensors : Dict[str, Any]
            a set of sensor_name, sensor pairs

        """
        route = "publish_discoveries"
        self.publisher_thread = MQTT_Publisher_Thread(self, self.device, self.smbus_device)
        self.__logger.debug('%s self.publisher_thread: %s', route, self.publisher_thread)
        self.publisher_thread.start()
        for key, sensor in sensors.items():
            self.publish_discovery(key, sensor)
        self.state.discovered = True
        self.__logger.debug('%s publisher_thread: %s', route, self.publisher_thread)

    def clear_discoveries(self, sensors:Dict[str, Any]) -> None:
        """ Publish a clear discovery message for each sensor in the device

        Parameters
        ----------
        sensors : Dict[str, Any]
            a set of sensor_name, sensor pairs

        """
        route = "clear_discoveries"
        self.__logger.debug('%s publisher_thread: %s', route, self.publisher_thread)
        for key, sensor in sensors.items():
            self.clear_discovery(key, sensor)
        self.state.discovered = False
        self.__logger.debug('%s self: %s', route, self)
        self.__logger.error('%s self.publisher_thread: %s', route, self.publisher_thread)
        self.publisher_thread.clear_do_run()
        self.publisher_thread.join()
        self.publisher_thread = None
        self.__logger.debug('%s self.publisher_thread: %s', route, self.publisher_thread)
