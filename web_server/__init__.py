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
        templates_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
        static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
        super().__init__(import_name, template_folder=templates_path, static_folder=static_path)
        self._register_routes()
        self.parser = parser
        self.__logger = logging.getLogger(__name__+'.'+self.__class__.__name__)
        self.client = client
        self.device = device
        secret_key = secrets.token_hex(32)
        self.config['SECRET_KEY'] = secret_key
        self.title = parser.title
        self.subtitle = parser.subtitle

    def _register_routes(self):
        @self.route('/', methods=['GET'])
        def index():
            route = f'{request.path} [{request.method}]'
            self.__logger.debug(f'{route} state: {self.client.state}')
            self.__logger.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
            if self.client.state.connected != self.client.is_connected():
                self.client.state.error = (
                    f"state.connected({self.client.state.connected}) does not match "
                    f"client.is_connected()({self.client.is_connected()})"
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
            self.__logger.debug(f'{route} - returning current state')
            return jsonify(self.client.state.to_dict())
        
        @self.route('/mqtt-toggle', methods=['POST'])
        def mqtt_toggle():
            route = f'{request.path} [{request.method}]'
            clientstate = request.get_json()
            self.client.state = State(clientstate)
            self.__logger.debug(f'%s state: %s -------------------', route, self.client.state.to_dict())
            if self.client.state.connected != self.client.is_connected():
                self.__logger.debug('%s resyncing client.is_connected(): %s, self.client.state: %s', route, self.client.is_connected(), self.client.state.to_dict())
                self.client.state = State()
                self.cllient.state.connected = self.client.is_connected()
                self.client.state.error = ['Web page reloaded, resyncing state']
                self.__logger.debug(f'%s state: %s', route, self.client.state.to_dict())
                return json.dumps(self.client.state.to_dict())
            if self.client.state.connected != self.client.is_connected():
                self.client.state.error = (f'state.connected({self.client.state.connected}) does not match client.is_connected()({self.client.is_connected()})')
                #return render_template('index.html', state=jsonify(self.client.state))
                return self.client.state
            if not self.client.state.discovered and not self.client.is_connected():
                # Connect and start loop
                self.__logger.debug(f'{route} connecting mqtt client')
                self.__logger.debug(f'{route} state: {self.client.state}, client.connect_mqtt()')
                self.client.connect_mqtt()
                self.__logger.debug(f'{route} client.loop_start()')
                self.client.loop_start()
                for _ in range(20):
                    self.__logger.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
                    if self.client.is_connected():
                        break
                    time.sleep(0.5)
                self.__logger.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
                self.client.state.connected = True
            elif not self.client.state.discovered:
                self.__logger.debug(f'{route} disconnecting mqtt client')
                self.__logger.debug(f'{route} state.discovered: {self.client.state.discovered}')
                if self.client.state.discovered:
                    # Discovery is still active, block disconnect
                    self.__logger.warning("{route} Cannot disconnect MQTT while discovery is enabled.")
                    # Optional: flash a message to user (see below)
                    flash("Disconnect blocked: Disable discovery first.")
                else:
                    self.__logger.debug(f'{route} loop_stop()')
                    self.client.loop_stop()
                    self.__logger.debug(f'{route} state: {self.client.state}, client.disconnect_mqtt()')
                    self.client.disconnect_mqtt()
                    self.client.state.connected = False
        
            self.__logger.debug(f'{route} return state: {self.client.state.to_dict()}')
            return json.dumps(self.client.state.to_dict())
        
        @self.route('/discovery-toggle', methods=['POST'])
        def discovery_toggle():
            route = f'{request.path} [{request.method}]'
        
            clientstate = request.get_json()
            self._stage = State(clientstate)
            self.__logger.debug(f'{route} ------------------------------------------------------------------------------------------------')
            self.__logger.debug(f'{route} clientstate: {clientstate}')
            self.client.state.connected = self.client.is_connected()
            self.client.state.discovered = clientstate.get('Discovered', self.client.state.discovered)
            self.client.state.error = []
            self.__logger.debug(f'{route} state: {self.client.state.to_dict()}')
        
            self.__logger.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
            if self.client.state.connected != self.client.is_connected():
                self.client.state.error = [f'state.connected({self.state.connected}) does not match client.is_connected()({self.client.is_connected()})']
                return str(self.client.state)
            if not self.client.state.discovered:
                # Turn ON
                self.__logger.debug(f'{route} turning on discovery')
                if not self.client.is_connected():
                    self.__logger.critical(f'{route} turning on discovery with client disconnected isn\'t going to work.')
                    #self.client.mqtt_connect()
                    #self.client.state.connected = True
                self.__logger.debug(f'{route} client.loop_start()')
                self.client.loop_start()
                self.__logger.debug(f'{route} client.publish_discoveries()')
                self.client.publish_discoveries(self.device.sensors)
        
                self.client.state.discovered = True
            else:
                # Turn OFF
                self.__logger.debug(f'{route} turning off discovery')
                self.__logger.debug(f'{route} client.clear_discoveries()')
                self.__logger.debug(f'{route} self.client {self.client}')
                self.client.clear_discoveries(self.device.sensors)
                self.__logger.debug(f'{route} time.sleep(0.5)')
                time.sleep(0.5)
                self.__logger.debug(f'{route} client.loop_stop()')
                self.client.loop_stop()
                self.client.state.discovered = False
        
            self.__logger.debug(f'{route} return state: {self.client.state.to_dict()}');
            return json.dumps(self.client.state.to_dict())
        
    # to handle ctrl-c, clear discoveries, and shut things down
    def shutdown_server(self):
        route = "Shutdown"
        self.__logger.info(f'Shutting down server')
        if self.client.state.discovered:
            self.__logger.info(f'{route} Clearing discovery')
            self.client.clear_discoveries(self.device.sensors)
            time.sleep(0.5)
            self.client.loop_stop()
            self.client.state.discovered = False
        else:
            self.__logger.info(f'{route} Not discovering')
        if self.client.state.connected:
            self.client.state.connected = False
            self.__logger.info(f'{route} Disconnecting MQTT')
            self.client.disconnect()
        else:
            self.__logger.info(f'{route} Not Connected')
