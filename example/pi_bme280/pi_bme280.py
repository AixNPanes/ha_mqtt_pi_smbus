import atexit
import logging

from example.pi_bme280.parsing import BME280Parser
from example.pi_bme280.device import BME280, BME280_Device
from ha_mqtt_pi_smbus.hamqtt_logging import loggerConfig
from ha_mqtt_pi_smbus.mqtt_client import MQTTClient
from ha_mqtt_pi_smbus.web_server import HAFlask

# parse config and command line args
parser = BME280Parser()
parser.parse_args()

# logger Setup
loggerConfig()
logger = logging.getLogger(__name__)

# BME280 Setup
bme280 = BME280(bus=parser.bme280.bus, address=parser.bme280.address)

# Device setup
device = BME280_Device(
    parser.bme280.sensor_name,
    "tph280/state",  # state topic
    "Bosch",  # manufacturer name
    "BME280",  # model name
    bme280,
    parser.bme280.polling_interval,
    parser.mqtt.expire_after,
)

# MQTT Setup
client = MQTTClient("bme280", device, bme280, parser.mqtt)

# define the Flask web server
app = HAFlask(__name__, parser, client, device)


# shutdown callback
def shutdown_server():
    logger.info("Shutting down server")
    app.shutdown_server()


if __name__ == "__main__":
    atexit.register(shutdown_server)  # register shutdown
    try:
        app.run(
                host=parser.web.address,
                port=parser.web.port,
                use_reloader=False)
    except Exception as e:
        print(e)
    except TypeError as e:
        print(e)
