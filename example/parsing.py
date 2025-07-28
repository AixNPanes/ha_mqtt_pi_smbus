import argparse
import logging
import socket
import sys
from typing import Any, Dict
import yaml

from ha_mqtt_pi_smbus.parsing import Parser, auto_int, configOrCmdParm

class BMEConfig:
    address: int
    bus: int
    sensor_name: str
    polling_interval: int

class BMEParser(Parser):
    def __init__(self):
        super().__init__()
        self.add_argument(
            "-a",
            "--bme280_address",
            help="BME280 address (118, 119, 0x67, 0x77",
            type=auto_int,
            choices=(118, 119),
        )
        self.add_argument(
            "-r",
            "--bme280_bus",
            help="BME280 I2C bus (1, 2)",
            type=int,
            choices=(1, 2)
        )        
        self.add_argument(
            "-N",
            "--bme280_sensor_name",
            help="BME280 Home Assistant sensor name",
            type=str,
        )
        self.add_argument(
            "-I",
            "--bme280_polling_interval",
            help="BME280 polling interval",
            type=int
        )

    def parse_args(self):
        self.args = super().parse_args()

        # get BME280 parameters
        self.bme = BMEConfig()
        bme = self.config['bme280'] if 'bme280' in self.config else []
        self.bme.bus = self.args.bme280_bus if self.args.bme280_bus \
            else bme['bus'] if 'bus' in bme else 1
        self.bme.address = self.args.bme280_address \
            if self.args.bme280_address \
            else bme['address'] if 'address' in bme else 0x76
        self.bme.sensor_name = \
            self.args.bme280_sensor_name if self.args.bme280_sensor_name \
               else bme['sensor_name'] if 'sensor_name' in bme else None
        self.bme.polling_interval = self.args.bme280_polling_interval \
            if self.args.bme280_polling_interval \
            else bme['polling_interval'] \
                if 'polling_interval' in bme else 60
        return self.args            
