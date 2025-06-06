from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import paho.mqtt.client as mqtt
import threading
import time
import json
import yaml
import logging
import random
import secrets
import sys
import atexit
import argparse
from parsing import Parser
from environ import MacAddress, CpuInfo, OSInfo
#from sensor import Sensor
from mqtt_client import MQTTClient
from bme_280 import BME_280
from bme280_sensor import BME280_Sensor
from hamqtt_logging import loggerConfig

# parse config and command line args
parser = Parser()

# logger Setup
loggerConfig(parser.logginglevelname)
logger = logging.getLogger(__name__)

# BME280 Setup
bme280 = BME_280(port=parser.bme280['port'], address=parser.bme280['address'])

# Sensor setup
sensor = BME280_Sensor(logger, parser.bme280['sensor_name'], bme280, parser.bme280['polling_interval'])

# MQTT Setup
client = MQTTClient('tph280', sensor, bme280, parser.mqtt)

# Flask web server setup
app = Flask(__name__)
app.logger.setLevel(parser.logginglevel)
logging.getLogger('werkzeug').setLevel(parser.logginglevel)
# Generate a secret key and set it in the app configuration
secret_key = secrets.token_hex(32)
app.config['SECRET_KEY'] = secret_key

# Flask template variables
state = {
        'Discovered': False,
        'Connected': False,
        'Error': '',}

# Flask web routing
@app.route('/', methods=['GET','POST'])
def index():
    global state,client
    route = f'{request.path} [{request.method}]'
    if request.method == 'POST':
        state = request.get_json()
    else:
        state = {'Connected': False, 'Discovered': False, 'Error': ''}
    logger.debug(f'{route} state: {state}')
    logger.debug(f'{route} client.is_connected(): {client.is_connected()}')
    if state['Connected'] != client.is_connected():
        state['Error'] = f'state[\'Connected\']({state["Connected"]}) does not match client.is_connected()({client.is_connected()})'
        return render_template('index.html', state=jsonify(state))
        #return jsonify(state)
    return render_template('index.html', state=state)

@app.route('/mqtt-toggle', methods=['POST'])
def mqtt_toggle():
    global state,client
    route = f'{request.path} [{request.method}]'
    state = request.get_json()
    logger.debug(f'{route} mqtt_toggle() state: {state} -------------------')
    logger.debug(f'{route} client.is_connected(): {client.is_connected()}')
    if state['Connected'] != client.is_connected():
        state['Error'] = f'state[\'Connected\']({state["Connected"]}) does not match client.is_connected()({client.is_connected()})'
        #return render_template('index.html', state=jsonify(state))
        return jsonify(state)
    if not state['Discovered'] and not client.is_connected():
        # Connect and start loop
        logger.debug(f'{route} connecting mqtt client')
        logger.debug(f'{route} state: {state}, client.connect_mqtt()')
        client.connect_mqtt()
        logger.debug(f'{route} client.loop_start()')
        client.loop_start()
        for _ in range(10):
            logger.debug(f'{route} client.is_connected(): {client.is_connected()}')
            if client.is_connected():
                break
            time.sleep(0.5)
        logger.debug(f'{route} client.is_connected(): {client.is_connected()}')
        state['Connected'] = True
    elif not state['Discovered']:
        logger.debug(f'{route} disconnecting mqtt client')
        logger.debug(f'{route} state["Discovered"]: {state["Discovered"]}')
        if state['Discovered']:
            # Discovery is still active, block disconnect
            logger.warning("{route} Cannot disconnect MQTT while discovery is enabled.")
            # Optional: flash a message to user (see below)
            flash("Disconnect blocked: Disable discovery first.")
        else:
            logger.debug(f'{route} loop_stop()')
            client.loop_stop()
            logger.debug(f'{route} state: {state}, client.disconnect_mqtt()')
            client.disconnect_mqtt()
            state['Connected'] = False

    logger.debug(f'{route} return jsonify(state): {state}')
    return jsonify(state)

@app.route('/discovery-toggle', methods=['POST'])
def discovery_toggle():
    global client,state
    route = f'{request.path} [{request.method}]'

    state = request.get_json()
    logger.debug(f'{route} state: {state}------------------------------------------------------------------------------------------------')

    logger.debug(f'{route} client.is_connected(): {client.is_connected()}')
    if state['Connected'] != client.is_connected():
        state['Error'] = f'state[\'Connected\']({state["Connected"]}) does not match client.is_connected()({client.is_connected()})'
        return jsonify(state)
    if not state['Discovered']:
        # Turn ON
        logger.debug(f'{route} turning on discovery')
        if not client.is_connected():
            logger.critical(f'{route} turning on discovery with client disconnected isn\'t going to work.')
            #client.mqtt_connect()
            #state['Connected'] = True
        logger.debug(f'{route} client.loop_start()')
        client.loop_start()
        logger.debug(f'{route} client.publish_discoveries()')
        client.publish_discoveries(sensor.devices)

        state['Discovered'] = True
    else:
        # Turn OFF
        logger.debug(f'{route} turning off discovery')
        logger.debug(f'{route} client.clear_discoveries()')
        client.clear_discoveries(sensor.devices)
        logger.debug(f'{route} time.sleep(0.5)')
        time.sleep(0.5)
        logger.debug(f'{route} client.loop_stop()')
        client.loop_stop()
        state['Discovered'] = False

    logger.debug(f'{route} return jsoinfy(state): {state}');
    return jsonify(state)

# to handle ctrl-c, clear discoveries, and shut things down
def shutdown_server():
    global state
    route = "Shutdown"
    logger.info(f'Shutting down server')
    if state['Discovered']:
        logger.info(f'{route} Clearing discovery')
        client.clear_discoveries(sensor.devices)
        time.sleep(0.5)
        client.loop_stop()
        state['Discovered'] = False
    else:
        logger.info(f'{route} Not discovering')
    if state['Connected']:
        state['Connected'] = False
        logger.info(f'{route} Disconnecting MQTT')
        client.disconnect()
    else:
        logger.info(f'{route} Not Connected')

if __name__ == '__main__':
    atexit.register(shutdown_server)
    debug = parser.logginglevel == 'DEBUG'
    app.run(debug=debug, host=parser.web['address'], port=parser.web['port'], use_reloader=False)
