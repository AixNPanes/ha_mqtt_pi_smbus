import atexit
import json
import logging
import os
import secrets
import threading
import time
import traceback

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from device import HADevice
from mqtt_client import MQTTClient, State

class HAFlask(Flask):
    def __init__(self, import_name, parser, client:MQTTClient, device:HADevice):
        route = '__init__'
        templates_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
        static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
        super().__init__(import_name, template_folder=templates_path, static_folder=static_path)
        self._register_routes()
        self.parser = parser
        self.__logger = logging.getLogger(__name__+'.'+self.__class__.__name__)
        self.client = client
        self.__logger.debug('%s self.client: %s', route, self.client)
        self.device = device
        secret_key = secrets.token_hex(32)
        self.config['SECRET_KEY'] = secret_key
        self.title = parser.title
        self.subtitle = parser.subtitle

    def _register_routes(self):
        @self.route('/', methods=['GET'])
        def index():
            route = f'{request.path} [{request.method}]'
            self.__logger.debug('%s state: %s', route, self.client.state)
            self.__logger.debug('%s client.is_connected(): %s', route, self.client.is_connected())
            if self.client.state.connected != self.client.is_connected():
                self.client.state.error = (
                    '%s state.connected(%s) does not match ' % (route, self.client.state.connected),
                    '%s client.is_connected()(%s)' % (route, self.client.is_connected())
                )
                return render_template(
                    'index.html',
                    state=self.client.state,
                    title=self.title,
                    subtitle=self.subtitle
                )
    
            return render_template(
                'index.html',
                state=self.client.state,
                title=self.title,
                subtitle=self.subtitle
            )

        @self.route('/status', methods=['GET'])
        def status():
            route = f'{request.path} [{request.method}]'
            self.__logger.debug('%s - returning current state', route)
            return jsonify(self.client.state.to_dict())
        
        @self.route('/mqtt-toggle', methods=['POST'])
        def mqtt_toggle():
            route = f'{request.path} [{request.method}]'
            clientstate = request.get_json()
            self.client.state = State(clientstate)
            self.__logger.debug('%s state: %s -------------------', route, self.client.state.to_dict())
            is_connected = self.client.is_connected()
            if self.client.state.connected != is_connected:
                self.__logger.debug('%s resyncing is_connected: %s, self.client.state: %s', route, is_connected, self.client.state.to_dict())
                self.client.state = State()
                self.client.state.connected = is_connected
                self.client.state.error = ['Web page reloaded, resyncing state']
                self.__logger.debug(f'%s state: %s', route, self.client.state.to_dict())
                return jsonify(self.client.state.to_dict())
            if self.client.state.connected != is_connected:
                self.client.state.error = (f'state.connected({self.client.state.connected}) does not match is_connected({is_connected})')
                #return render_template('index.html', state=jsonify(self.client.state))
                return self.client.state
            if not self.client.state.discovered and not is_connected:
                # Connect and start loop
                self.__logger.debug('%s connecting mqtt client', route)
                self.__logger.debug('%s state: %s', route, self.client.state)
                self.client.connect_mqtt()
                self.__logger.debug('%s client.loop_start()', route)
                self.client.loop_start()
                for _ in range(20):
                    is_connected = self.client.is_connected()
                    self.__logger.debug('%s is_connected: %s', route, is_connected)
                    if is_connected:
                        break
                    time.sleep(0.5)
                self.__logger.debug('%s is_connected: %s', route, is_connected)
                self.client.state.connected = True
            elif not self.client.state.discovered:
                self.__logger.debug('%s disconnecting mqtt client', route)
                self.__logger.debug('%s state.discovered: %s', route, self.client.state.discovered)
                if self.client.state.discovered:
                    # Discovery is still active, block disconnect
                    self.__logger.warning('%s Cannot disconnect MQTT while discovery is enabled.', route)
                    # Optional: flash a message to user (see below)
                    flash("Disconnect blocked: Disable discovery first.")
                else:
                    self.__logger.debug('%s loop_stop()', route)
                    self.client.loop_stop()
                    self.__logger.debug('%s state: %s', route, self.client.state)
                    self.client.disconnect_mqtt()
                    self.client.state.connected = False

            self.__logger.debug('%s return state: %s', route, self.client.state.to_dict())
            return jsonify(self.client.state.to_dict())

        @self.route('/discovery-toggle', methods=['POST'])
        def discovery_toggle():
            route = f'{request.path} [{request.method}]'

            clientstate = request.get_json()
            self._stage = State(clientstate)
            self.__logger.debug('%s ------------------------------------------------------------------------------------------------', route)
            self.__logger.debug('%s clientstate: %s', route, clientstate)
            self.client.state.error = []
            connected = self.client.is_connected()
            self.__logger.debug('%s client.state.connected: %s', route, self.client.state.connected)

            self.__logger.debug('%s connected: %s', route, connected)
            if self.client.state.connected != connected:
                self.client.state.error = ['client connected state mismatch']
                #self.client.state.connected = connected
                #self.client.state.discovered = False
                self.__logger.debug('%s %s', route, self.client.state.error)
                return jsonify(self.client.state.to_dict())
            if not self.client.state.connected:
                self.client.state.error = ['client must be connected']
                self.client.state.connected = False
                self.client.state.discovered = False
                self.__logger.debug('%s %s', route, self.client.state.error)
                return jsonify(self.client.state.to_dict())
            if not self.client.state.discovered:
                # Turn ON
                self.__logger.debug('%s turning on discovery', route)
                self.__logger.debug('%s client.loop_start()', route)
                self.client.loop_start()
                self.__logger.debug('%s client.publish_discoveries()', route)
                self.client.publish_discoveries(self.device.sensors)
                self.client.state.discovered = True
            else:
                # Turn OFF
                self.__logger.debug('%s turning off discovery', route)
                self.__logger.debug('%s client.clear_discoveries()', route)
                self.__logger.debug('%s self.client %s',route, self.client)
                self.client.clear_discoveries(self.device.sensors)
                self.__logger.debug('%s time.sleep(0.5)', route)
                time.sleep(0.5)
                self.__logger.debug('%s client.loop_stop()', route)
                self.client.loop_stop()
                self.client.state.discovered = False
            self.__logger.debug('%s return state: %s', route, self.client.state.to_dict())
            return jsonify(self.client.state.to_dict())

    # to handle ctrl-c, clear discoveries, and shut things down
    def shutdown_server(self):
        route = "Shutdown"
        self.__logger.info('%s Shutting down server', route)
        if self.client.state.discovered:
            self.__logger.info('%s Clearing discovery', route)
            self.client.clear_discoveries(self.device.sensors)
            time.sleep(0.5)
            self.client.loop_stop()
            self.client.state.discovered = False
        else:
            self.__logger.info('%s Not discovering', route)
        if self.client.state.connected:
            self.client.state.connected = False
            self.__logger.info('%s Disconnecting MQTT', route)
            self.client.disconnect()
        else:
            self.__logger.info('%s Not Connected', route)
