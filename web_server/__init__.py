import atexit
import json
import logging
import os
import secrets
import threading
import time

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from ha_device import HADevice
from mqtt_client import MQTTClient

class HAFlask(Flask):
    def __init__(self, import_name, parser, logger, client:MQTTClient, device:HADevice):
        templates_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
        static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
        super().__init__(import_name, template_folder=templates_path, static_folder=static_path)
        self._register_routes()
        self.parser = parser
        self.logger.setLevel(parser.logginglevel)
        self.logger_ = logging.getLogger(self.__class__.__name__)
        self.client = client
        self.device = device
        logging.getLogger('werkzeug').setLevel(parser.logginglevel)
        secret_key = secrets.token_hex(32)
        self.config['SECRET_KEY'] = secret_key
        self.title = parser.title
        # Flask template variables
        self.state = {
                'Discovered': False,
                'Connected': False,
                'Error': '',}

    def _register_routes(self):
        @self.route('/', methods=['GET','POST'])
        def index():
            route = f'{request.path} [{request.method}]'
            if request.method == 'POST':
                self.state = request.get_json()
            else:
                self.state = {'Connected': False, 'Discovered': False, 'Error': ''}
            self.logger_.debug(f'{route} state: {self.state}')
            self.logger_.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
            self.logger_.debug(f'{route} title: {self.title}')
            if self.state['Connected'] != self.client.is_connected():
                self.state['Error'] = f'state[\'Connected\']({self.state["Connected"]}) does not match client.is_connected()({self.client.is_connected()})'
                return render_template('index.html', state=jsonify(self.state), variable_title=self.title)
                #return jsonify(self.state)
            return render_template('index.html', state=self.state, variable_title=self.title)
        
        @self.route('/mqtt-toggle', methods=['POST'])
        def mqtt_toggle():
            route = f'{request.path} [{request.method}]'
            self.state = request.get_json()
            self.logger_.debug(f'{route} mqtt_toggle() state: {self.state} -------------------')
            self.logger_.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
            if self.state['Connected'] != self.client.is_connected():
                self.state['Error'] = f'state[\'Connected\']({self.state["Connected"]}) does not match client.is_connected()({self.client.is_connected()})'
                #return render_template('index.html', state=jsonify(self.state))
                return jsonify(self.state)
            if not self.state['Discovered'] and not self.client.is_connected():
                # Connect and start loop
                self.logger_.debug(f'{route} connecting mqtt client')
                self.logger_.debug(f'{route} state: {self.state}, client.connect_mqtt()')
                self.client.connect_mqtt()
                self.logger_.debug(f'{route} client.loop_start()')
                self.client.loop_start()
                for _ in range(20):
                    self.logger_.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
                    if self.client.is_connected():
                        break
                    time.sleep(0.5)
                self.logger_.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
                self.state['Connected'] = True
            elif not self.state['Discovered']:
                self.logger_.debug(f'{route} disconnecting mqtt client')
                self.logger_.debug(f'{route} state["Discovered"]: {self.state["Discovered"]}')
                if self.state['Discovered']:
                    # Discovery is still active, block disconnect
                    self.logger_.warning("{route} Cannot disconnect MQTT while discovery is enabled.")
                    # Optional: flash a message to user (see below)
                    flash("Disconnect blocked: Disable discovery first.")
                else:
                    self.logger_.debug(f'{route} loop_stop()')
                    self.client.loop_stop()
                    self.logger_.debug(f'{route} state: {self.state}, client.disconnect_mqtt()')
                    self.client.disconnect_mqtt()
                    self.state['Connected'] = False
        
            self.logger_.debug(f'{route} return jsonify(state): {self.state}')
            return jsonify(self.state)
        
        @self.route('/discovery-toggle', methods=['POST'])
        def discovery_toggle():
            route = f'{request.path} [{request.method}]'
        
            self.state = request.get_json()
            self.logger_.debug(f'{route} state: {self.state}------------------------------------------------------------------------------------------------')
        
            self.logger_.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
            if self.state['Connected'] != self.client.is_connected():
                self.state['Error'] = f'state[\'Connected\']({self.state["Connected"]}) does not match client.is_connected()({self.client.is_connected()})'
                return jsonify(self.state)
            if not self.state['Discovered']:
                # Turn ON
                self.logger_.debug(f'{route} turning on discovery')
                if not self.client.is_connected():
                    self.logger_.critical(f'{route} turning on discovery with client disconnected isn\'t going to work.')
                    #self.client.mqtt_connect()
                    #self.state['Connected'] = True
                self.logger_.debug(f'{route} client.loop_start()')
                self.client.loop_start()
                self.logger_.debug(f'{route} client.publish_discoveries()')
                self.client.publish_discoveries(self.device.sensors)
        
                self.state['Discovered'] = True
            else:
                # Turn OFF
                self.logger_.debug(f'{route} turning off discovery')
                self.logger_.debug(f'{route} client.clear_discoveries()')
                self.client.clear_discoveries(self.device.sensors)
                self.logger_.debug(f'{route} time.sleep(0.5)')
                time.sleep(0.5)
                self.logger_.debug(f'{route} client.loop_stop()')
                self.client.loop_stop()
                self.state['Discovered'] = False
        
            self.logger_.debug(f'{route} return jsoinfy(state): {self.state}');
            return jsonify(self.state)
        
    # to handle ctrl-c, clear discoveries, and shut things down
    def shutdown_server(self):
        route = "Shutdown"
        self.logger_.info(f'Shutting down server')
        if self.state['Discovered']:
            self.logger_.info(f'{route} Clearing discovery')
            self.client.clear_discoveries(self.device.sensors)
            time.sleep(0.5)
            self.client.loop_stop()
            self.state['Discovered'] = False
        else:
            self.logger_.info(f'{route} Not discovering')
        if self.state['Connected']:
            self.state['Connected'] = False
            self.logger_.info(f'{route} Disconnecting MQTT')
            self.client.disconnect()
        else:
            self.logger_.info(f'{route} Not Connected')
