import atexit
import logging

import paho.mqtt.client as mqtt

from parsing import Parser
from mqtt_client import MQTTClient
from bme_280 import BME_280
from bme280_device import BME280_Device
from hamqtt_logging import loggerConfig
from web_server import HAFlask

# parse config and command line args
parser = Parser()

# logger Setup
loggerConfig(parser.logginglevelname)
logger = logging.getLogger(__name__)

# BME280 Setup
bme280 = BME_280(bus=parser.bme280['bus'], address=parser.bme280['address'])

# Device setup
device = BME280_Device(logger, parser.bme280['sensor_name'], bme280, parser.bme280['polling_interval'])

# MQTT Setup
client = MQTTClient('tph280', device, bme280, parser.mqtt)

app = HAFlask(__name__, parser, logger, client, device)

def shutdown_server():
    app.shutdown_server()                 

if __name__ == '__main__':
    atexit.register(shutdown_server)
    debug:bool = parser.logginglevel == 'DEBUG'
    app.run(debug=debug, host=parser.web['address'], port=parser.web['port'], use_reloader=False)
