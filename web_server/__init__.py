import atexit
import json
import logging
import os
import secrets
import threading
import time

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from device import HADevice
from mqtt_client import MQTTClient

class _State:
    connected:bool = False
    discovered:bool = False
    error:str = ""

    def __init__(self, obj:dict = None):
        if obj is None:
            return
        if 'Connected' in obj:
            self.connected = obj['Connected']
        if 'Discovered' in obj:
            self.discovered = obj['Discovered']
        if 'Error' in obj:
            self.error = obj['Error']

    def to_dict(self):
        return { 
            "Connected": self.connected, 
            "Discovered": self.discovered, 
            "Error": self.error}

class HAFlask(Flask):
    def __init__(self, import_name, parser, client:MQTTClient, device:HADevice):
        templates_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
        static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
        super().__init__(import_name, template_folder=templates_path, static_folder=static_path)
        self._register_routes()
        self.parser = parser
        self.__logger = logging.getLogger(__name__+'.'+self.__class__.__name__)
        self.client = client
        self._state = _State() 
        self.device = device
        secret_key = secrets.token_hex(32)
        self.config['SECRET_KEY'] = secret_key
        self.title = parser.title
        self.subtitle = parser.subtitle

    def _register_routes(self):
        @self.route('/', methods=['GET'])
        def index():
            route = f'{request.path} [{request.method}]'
            self.__logger.debug(f'{route} state: {self._state}')
            self.__logger.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
    
            if self._state.connected != self.client.is_connected():
                self._state.error = (
                    f"_state.connected({self._state.connected}) does not match "
                    f"client.is_connected()({self.client.is_connected()})"
                )
                return render_template(
                    'index.html',
                    state=self._state,
                    title=self.title,
                    subtitle=self.subtitle
                )
    
            return render_template(
                'index.html',
                state=self._state,
                title=self.title,
                subtitle=self.subtitle
            )

        @self.route('/status', methods=['GET'])
        def status():
            route = f'{request.path} [{request.method}]'
            self.__logger.debug(f'{route} - returning current state')
            return jsonify(self._state.to_dict())
        
        @self.route('/mqtt-toggle', methods=['POST'])
        def mqtt_toggle():
            route = f'{request.path} [{request.method}]'
            client_state = request.get_json()
            self._state = _State(client_state)
            if self._state.connected != self.client.is_connected():
                raise Exception("state error")
            self.__logger.debug(f'{route} _state: {self._state} -------------------')
            if self._state.connected != self.client.is_connected():
                self._state.error = f'_state.connected({self._state.connected}) does not match client.is_connected()({self.client.is_connected()})'
                #return render_template('index.html', state=jsonify(self._state))
                return self._state
            if not self._state.discovered and not self.client.is_connected():
                # Connect and start loop
                self.__logger.debug(f'{route} connecting mqtt client')
                self.__logger.debug(f'{route} state: {self._state}, client.connect_mqtt()')
                self.client.connect_mqtt()
                self.__logger.debug(f'{route} client.loop_start()')
                self.client.loop_start()
                for _ in range(20):
                    self.__logger.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
                    if self.client.is_connected():
                        break
                    time.sleep(0.5)
                self.__logger.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
                self._state.connected = True
            elif not self._state.discovered:
                self.__logger.debug(f'{route} disconnecting mqtt client')
                self.__logger.debug(f'{route} _state.discovered: {self._state.discovered}')
                if self._state.discovered:
                    # Discovery is still active, block disconnect
                    self.__logger.warning("{route} Cannot disconnect MQTT while discovery is enabled.")
                    # Optional: flash a message to user (see below)
                    flash("Disconnect blocked: Disable discovery first.")
                else:
                    self.__logger.debug(f'{route} loop_stop()')
                    self.client.loop_stop()
                    self.__logger.debug(f'{route} state: {self._state}, client.disconnect_mqtt()')
                    self.client.disconnect_mqtt()
                    self._state.connected = False
        
            self.__logger.debug(f'{route} return _state: {self._state.to_dict()}')
            return json.dumps(self._state.to_dict())
        
        @self.route('/discovery-toggle', methods=['POST'])
        def discovery_toggle():
            route = f'{request.path} [{request.method}]'
        
            client_state = request.get_json()
            self._stage = _State(client_state)
            self.__logger.debug(f'{route} ------------------------------------------------------------------------------------------------')
            self.__logger.debug(f'{route} client_state: {client_state}')
            self._state.connected = self.client.is_connected()
            self._state.discovered = client_state.get('Discovered', self._state.discovered)
            self._state.error = ''
            self.__logger.debug(f'{route} state: {self._state.to_dict()}')
        
            self.__logger.debug(f'{route} client.is_connected(): {self.client.is_connected()}')
            if self._state.connected != self.client.is_connected():
                self._state.error = f'_state.connected({self._state.connected}) does not match client.is_connected()({self.client.is_connected()})'
                return str(self._state)
            if not self._state.discovered:
                # Turn ON
                self.__logger.debug(f'{route} turning on discovery')
                if not self.client.is_connected():
                    self.__logger.critical(f'{route} turning on discovery with client disconnected isn\'t going to work.')
                    #self.client.mqtt_connect()
                    #self._state.connected = True
                self.__logger.debug(f'{route} client.loop_start()')
                self.client.loop_start()
                self.__logger.debug(f'{route} client.publish_discoveries()')
                self.client.publish_discoveries(self.device.sensors)
        
                self._state.discovered = True
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
                self._state.discovered = False
        
            self.__logger.debug(f'{route} return _state: {self._state.to_dict()}');
            return json.dumps(self._state.to_dict())
        
    # to handle ctrl-c, clear discoveries, and shut things down
    def shutdown_server(self):
        route = "Shutdown"
        self.__logger.info(f'Shutting down server')
        if self._state.discovered:
            self.__logger.info(f'{route} Clearing discovery')
            self.client.clear_discoveries(self.device.sensors)
            time.sleep(0.5)
            self.client.loop_stop()
            self._state.discovered = False
        else:
            self.__logger.info(f'{route} Not discovering')
        if self._state.connected:
            self._state.connected = False
            self.__logger.info(f'{route} Disconnecting MQTT')
            self.client.disconnect()
        else:
            self.__logger.info(f'{route} Not Connected')
