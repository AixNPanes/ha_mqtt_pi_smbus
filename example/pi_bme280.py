import atexit
import logging
import os

import paho.mqtt.client as mqtt

from example.parsing import Parser
from example.device import BME280, BME280_Device
from hamqtt_logging import loggerConfig
from mqtt_client import MQTTClient
from web_server import HAFlask

# parse config and command line args
parser = Parser()
    
# logger Setup
loggerConfig()
logger = logging.getLogger(__name__)

# BME280 Setup
bme280 = BME280(
    bus=parser.bme280['bus'],
    address=parser.bme280['address'])

# Device setup
device = BME280_Device(
    parser.bme280['sensor_name'],
    'bme280/state',             # state topic
    'Bosch',                    # manufacturer name
    'BME280',                   # model name
    bme280,
    parser.bme280['polling_interval'])

# MQTT Setup
client = MQTTClient(
    'bme280',                   # MQTT clent nameix
    device,
    bme280,
    parser.mqtt)

# define the Flask web server
app = HAFlask(__name__, parser, client, device)


# shutdown callback
def shutdown_server():
    logger.info('Shutting down server')
    app.shutdown_server()

if __name__ == '__main__':
    atexit.register(shutdown_server)            # register shutdown
    try:
        app.run(
            host=parser.web['address'],
            port=parser.web['port'],
            use_reloader=False)
    except Exception as e:
        print(e)
    except TypeError as e:
        print(e)
