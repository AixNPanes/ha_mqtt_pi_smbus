from __future__ import annotations

import json
import logging
import random
import threading
import time

import paho

from bme_280 import BME_280
from device import HADevice
from environ import MacAddress

class MQTT_Publisher_Thread(threading.Thread):
    def __init__(self, client:"MQTTClient", device: HADevice, bme280:BME_280):
        super().__init__(name='MQTT_Publisher', daemon=True)
        self.client = client
        self.device = device
        self.bme280 = bme280
        self.__logger = logging.getLogger('MQTT_Publisher_Thread')
        self.do_run = True
        self.data = self.bme280.data()

    def run(self):
        while True:
            if not self.do_run:
                return
            data = self.bme280.data()
            if data['last_update'] != self.data['last_update']:
                self.data = data
                self.client.publish(self.device.state_topic, json.dumps(data))
                self.__logger.debug(f"MQTT publisher: {json.dumps(data, indent=4)}")
            time.sleep(1)

    def clear_do_run(self):
        self.do_run = False

class MQTTClient(paho.mqtt.client.Client):
    def on_connect(client, userdata, flags, rc, properties=None):
        """Callback function called when the client connects to the broker."""
        client.status['rc'] = rc
        if rc == 0:
            client.status['connected'] = True
        else:
            client.status['error'] = connack_string(rc)
            
    def init_status(self):
        self.status = {
             "connected": False,
             "rc": None,
             "error": None
        }

    def __init__(self, client_prefix:str, device:HADevice, bme280:BME_280, mqtt_config:dict = None):
        super().__init__(
                paho.mqtt.enums.CallbackAPIVersion.VERSION2, 
                f'{client_prefix}-{MacAddress.getObjectId()}-{str(random.randint(0,1000)).zfill(3)}',
                True, None)
        self.broker_address = mqtt_config['broker']
        self.port = mqtt_config['port']
        self.username = mqtt_config['username']
        self.password = mqtt_config['password']
        self.device = device
        self.bme280 = bme280
        self.init_status()
        self.connected = False
        self.connected_flag = False
        self.on_connect = MQTTClient.on_connect
        #self.on_disconnect = self._on_disconnect
        self.publisher_thread = None
        super().enable_logger(self.logger)
        super().user_data_set(self)
        self.__logger = logging.getLogger('MQTTClient')

    def connect_mqtt(self):
        route = "connect_mqtt"
        super().username_pw_set(self.username, self.password)
        print(self.username+"/"+self.password+"/"+self.broker_address+"/"+str(self.port))
        self.init_status()
        mqttErrorCode = super().connect(self.broker_address, self.port)
        if mqttErrorCode != 0:
            self.__logger.critical(f'{route} error {mqttErrorCode} in connect_mqtt')
        self.__logger.info(f"{route} connecting to broker at {self.broker_address}:{self.port}")

    def disconnect_mqtt(self):
        route = "disconnect_mqtt"
        mqttErrorCode = super().disconnect()
        if mqttErrorCode != 0:
            self.__logger.critical(f'{route} error {mqttErrorCode} in disconnect_mqtt')


    def subscribe(self, topic):
        route = "subscribe"
        self.__logger.info(f'{route} subscribing to topic "{topic}"')
        tuple = super().subscribe(topic)
        return tuple

    def publish(self, topic, message, qos: int = 0, retain: bool = False,
                properties: paho.mqtt.properties.Properties | None = None):
        route = "publish"
        self.__logger.info(f'{route} publishing to topic: "{topic}"')
        self.__logger.debug(f'{route} \tmessage: "{message}"')
        result = super().publish(topic, message)
        status = result[0]
        mid = result[1]
        if status == 0:
            self.__logger.debug(f'{route} Sent "{message}" to "{topic}" with mid: {mid}')
            pass
        else:
            self.__logger.error(f"{route} Failed to send message to topic {topic}, rc {status}")
            pass
        return result

    def publish_discovery(self, key:str, device:dict):
        route = "publish_discovery"
        self.publish(
                device.discovery_topic, 
                json.dumps(device.discovery_payload), 
                qos=2, retain=True)
        self.__logger.info(f"{route} Published discovery for {key}")

    def clear_discovery(self, key:str, device:dict):
        route = "clear_discovery"
        self.publish(device.discovery_topic, "", qos=2, retain=True)
        self.__logger.info(f"{route} Cleared discovery for {key}")

    def publish_discoveries(self, devices:dict):
        self.publisher_thread = MQTT_Publisher_Thread(self, self.device, self.bme280)
        self.publisher_thread.start()
        for key, device in devices.items():
            self.publish_discovery(key, device)

    def clear_discoveries(self, devices:dict):
        for key, device in devices.items():
            self.clear_discovery(key, device)
        self.publisher_thread.clear_do_run()
        self.publisher_thread.join()
        self.publisher_thread = None
