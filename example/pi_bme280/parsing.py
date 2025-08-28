import logging
from typing import Any, Dict

from ha_mqtt_pi_smbus.config import Config
from ha_mqtt_pi_smbus.parsing import Parser
from ha_mqtt_pi_smbus.util import auto_int


class BME280Parser(Parser):
    """Parse BME280 specific parameters and merge with config files
    """
    def __init__(self):
        super().__init__()
        self.add_argument(
            "-a",
            "--bme280_address",
            help="BME280 address (118, 119, 0x76, 0x77",
            type=auto_int,
            choices=(118, 119),
        )
        self.add_argument(
            "-r", "--bme280_bus", help="BME280 I2C bus (1, 2)", type=int, choices=(1, 2)
        )
        self.add_argument(
            "-N",
            "--bme280_sensor_name",
            help="BME280 Home Assistant sensor name",
            type=str,
        )
        self.add_argument(
            "-I", "--bme280_polling_interval", help="BME280 polling interval", type=int
        )

    def parse_args(self):
        """Parse commandline arguments and merge with config files"""
        super().parse_args()

        # get BME280 parameters
        bme280 = {}
        if self.args.bme280_bus is not None:
            bme280["bus"] = self.args.bme280_bus
        if self.args.bme280_address is not None:
            bme280["address"] = self.args.bme280_address
        if self.args.bme280_sensor_name is not None:
            bme280["sensor_name"] = self.args.bme280_sensor_name
        if self.args.bme280_polling_interval is not None:
            bme280["polling_interval"] = self.args.bme280_polling_interval
        self._config_dict['bme280'] = bme280    


class Bme280Config():
    address: int
    bus: int
    sensor_name: str
    polling_interval: int

    #def __init__(self, args:Dict[str, Any] = None):
    #    if 'args' == None:
    #        return
    #    logging.getLogger(__name__).error(args)
    #    if 'bme280' not in args:
    #        return
    #    bme280 = args['bme280']
    #    if 'bus' in bme280:
    #        self.bus = bme280['bus']
    #    if 'address' in bme280:
    #        self.address = bme280['address']
    #    if 'sensor_name' in bme280:
    #        self.sensor_name = bme280['sensor_name']
    #    if 'polling_interval' in bme280:
    #        self.polling_interval = bme280['polling_interval']
    #    logging.getLogger(__name__).error(self.__dict__)


    def clone(self):
        config = Bme280Config()
        config.bus = self.bus
        config.address = self.address
        config.sensor_name = self.sensor_name
        config.polling_interval = self.polling_interval

    def sanitize(self):
        return self
