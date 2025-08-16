import argparse
import logging
import socket
import sys
from typing import Any, Dict
import yaml

from ha_mqtt_pi_smbus.parsing import Parser, auto_int


class BME280Config:
    address: int
    bus: int
    sensor_name: str
    polling_interval: int


class BME280Parser(Parser):
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
        self.args = super().parse_args()

        # get BME280 parameters
        self.bme280 = BME280Config()
        bme280 = self.config["bme280"] if "bme280" in self.config else []
        self.bme280.bus = (
            self.args.bme280_bus
            if self.args.bme280_bus
            else bme280["bus"] if "bus" in bme280 else 1
        )
        self.bme280.address = (
            self.args.bme280_address
            if self.args.bme280_address
            else bme280["address"] if "address" in bme280 else 0x76
        )
        self.bme280.sensor_name = (
            self.args.bme280_sensor_name
            if self.args.bme280_sensor_name
            else bme280["sensor_name"] if "sensor_name" in bme280 else None
        )
        self.bme280.polling_interval = (
            self.args.bme280_polling_interval
            if self.args.bme280_polling_interval
            else bme280["polling_interval"] if "polling_interval" in bme280 else 60
        )
        return self.args
