import atexit
import json
import logging
import os
import secrets
import threading
import time
import traceback

import pdb

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from ha_mqtt_pi_smbus.device import HADevice
from ha_mqtt_pi_smbus.mqtt_client import MQTTClient


class HAFlask(Flask):
    def __init__(
        self,
        import_name,
        parser,
        client: MQTTClient,
        device: HADevice,
        _debug_step_count: int = 20,
    ):
        route = "__init__"
        templates_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "templates")
        )
        static_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "static")
        )
        super().__init__(
            import_name, template_folder=templates_path, static_folder=static_path
        )
        self._debug_step_count = _debug_step_count
        self._register_routes()
        self.parser = parser
        self.__logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.client = client
        self.device = device
        secret_key = secrets.token_hex(32)
        self.config["SECRET_KEY"] = secret_key
        self.title = parser.title
        self.subtitle = parser.subtitle

    def _register_routes(self):
        @self.route("/", methods=["GET"])
        def index():
            route = f"{request.path} [{request.method}]"

            return render_template(
                "index.html",
                state=self.client.state.to_dict(),
                title=self.title,
                subtitle=self.subtitle,
            )

        @self.route("/status", methods=["GET"])
        def status():
            route = f"{request.path} [{request.method}]"
            return jsonify(self.client.state.to_dict())
            # return render_template(
            #    "index.html",
            #    state=self.client.state.to_dict(),
            #    title=self.title,
            #    subtitle=self.subtitle,
            # )

        @self.route("/mqtt-toggle", methods=["POST"])
        def mqtt_toggle():
            route = f"{request.path} [{request.method}]"
            state = self.client.state.validate(
                request.get_json(), self.client.is_connected()
            )
            json_data = request.get_json()
            is_connected = state.connected
            if not is_connected:
                # Connect and start loop
                self.client.connect_mqtt()
                self.client.loop_start()
                for _ in range(self._debug_step_count):
                    is_connected = self.client.is_connected()
                    if is_connected:
                        self.client.state.connected = True
                        break
                    time.sleep(0.5)
                return jsonify(self.client.state.to_dict())
            self.client.disconnect_mqtt()
            self.client.state.connected = False
            return jsonify(self.client.state.to_dict())

        @self.route("/discovery-toggle", methods=["POST"])
        def discovery_toggle():
            route = f"{request.path} [{request.method}]"
            clientstate = request.get_json()
            self.client.state.error = []
            is_connected = self.client.is_connected()

            if not self.client.state.discovered:
                # Turn ON
                self.client.loop_start()
                self.client.publish_discoveries(self.device.sensors)
                self.client.state.discovered = True
            else:
                # Turn OFF
                self.client.clear_discoveries(self.device.sensors)
                time.sleep(0.5)
                self.client.loop_stop()
                self.client.state.discovered = False
            return jsonify(self.client.state.to_dict())

    # to handle ctrl-c, clear discoveries, and shut things down
    def shutdown_server(self):
        route = "Shutdown"
        self.__logger.info("%s Shutting down server", route)
        if self.client.state.discovered:
            self.__logger.info("%s Clearing discovery", route)
            self.client.clear_discoveries(self.device.sensors)
            time.sleep(0.5)
            self.client.loop_stop()
            self.client.state.discovered = False
        else:
            self.__logger.info("%s Not discovering", route)
        if self.client.state.connected:
            self.client.state.connected = False
            self.__logger.info("%s Disconnecting MQTT", route)
            self.client.disconnect()
        else:
            self.__logger.info("%s Not Connected", route)
