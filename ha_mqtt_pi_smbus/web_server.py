import logging
import os
import secrets
import time

from flask import Flask, render_template, request, jsonify

from ha_mqtt_pi_smbus.device import HADevice
from ha_mqtt_pi_smbus.mqtt_client import MQTTClient


class HAFlask(Flask):
    """Wrap the Flask class to provide functons for MQTT

    Parameters
    ----------
    import_name : str
        the Flask import_name
    parser : ha_mqtt_pi_smbus.parsing.AParser
        the parser variable from which to retrieve configuration
    client : ha_mqtt_pi_smbus.mqtt_client.MQTTClient
        the MQTT client to us to commuicate with the MQTT broker
    device : ha_mqtt_pi_smbus.device.HADevice
        the SMBus device which is to be presented to Home Assistant
    _debug_step_count : int
        the maximum number of .5 second intervals over which the web
        server will wait before giving put.  Default 20,
    """

    def connect(self):
        """Connect to the MQTT broker

        Parameters
        ----------
        None
        """
        # Connect and start loop
        self.client.connect_mqtt()
        self.client.loop_start()
        for _ in range(self._debug_step_count):
            is_connected = self.client.is_connected()
            if is_connected:
                self.client.state.connected = True
                break
            time.sleep(0.5)

    def discover(self):
        """Send discovery payload to MQTT broker

        Parameters
        ----------
        None
        """
        # Turn ON
        self.client.loop_start()
        self.client.publish_discovery(self.device)
        self.client.state.discovered = True
        self.client.publish_available(self.device)

    def __init__(
        self,
        import_name,
        parser,
        client: MQTTClient,
        device: HADevice,
        _debug_step_count: int = 20,
    ):
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
        self.config.SECRET_KEY = secret_key
        self.title = parser.title
        self.subtitle = parser.subtitle
        if parser.mqtt.auto_discover:
            self.connect()
            self.discover()

    def _register_routes(self):
        """Define the Flask web routes"""

        @self.route("/", methods=["GET"])
        def index():
            return render_template(
                "index.html",
                state=self.client.state.to_dict(),
                title=self.title,
                subtitle=self.subtitle,
            )

        @self.route("/status", methods=["GET"])
        def status():
            return jsonify(self.client.state.to_dict())

        @self.route("/mqtt-toggle", methods=["POST"])
        def mqtt_toggle():
            state = self.client.state.validate(
                request.get_json(), self.client.is_connected()
            )
            is_connected = state.connected
            if not is_connected:
                self.connect()
                return jsonify(self.client.state.to_dict())
            self.client.disconnect_mqtt()
            self.client.state.connected = False
            return jsonify(self.client.state.to_dict())

        @self.route("/discovery-toggle", methods=["POST"])
        def discovery_toggle():
            self.client.state.error = []

            if not self.client.state.discovered:
                self.discover()
            else:
                # Turn OFF
                self.client.publish_not_available(self.device)
                time.sleep(0.5)
                self.client.clear_discovery(self.device)
                time.sleep(0.5)
                self.client.loop_stop()
                self.client.state.discovered = False
            return jsonify(self.client.state.to_dict())

    def shutdown_server(self):
        """Handle ctrl-c, clear discoveries, and shut things down

        Parameters
        ----------
        None
        """
        route = "Shutdown"
        self.__logger.info("%s Shutting down server", route)
        if self.client.state.discovered:
            self.__logger.info("%s Clearing discovery", route)
            self.client.clear_discovery(self.device)
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
