import logging
from pathlib import Path
from unittest.mock import MagicMock, mock_open

MOCK_OSRELEASE_DATA = '''PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
NAME="Debian GNU/Linux"
VERSION_ID="12"
VERSION="12 (bookworm)"
VERSION_CODENAME=bookworm
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"'''

MOCK_CPUINFO_DATA = """processor	: 0
BogoMIPS	: 38.40
Features	: fp asimd evtstrm crc32 cpuid
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd03
CPU revision	: 4

processor	: 1
BogoMIPS	: 38.40
Features	: fp asimd evtstrm crc32 cpuid
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd03
CPU revision	: 4

processor	: 2
BogoMIPS	: 38.40
Features	: fp asimd evtstrm crc32 cpuid
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd03
CPU revision	: 4

processor	: 3
BogoMIPS	: 38.40
Features	: fp asimd evtstrm crc32 cpuid
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd03
CPU revision	: 4

Revision	: a22082
Serial		: 000000009ec1f24d
Model		: Raspberry Pi 3 Model B Rev 1.2"""

MOCK_SYS_CLASS_THERMAL_THERMAL_ZONE0_TEMP = """46160
"""

MOCK_IFCONFIG_WLAN0_DATA = """wlan0: flags=4098<BROADCAST,MULTICAST>  mtu 1500
        ether b8:27:eb:94:a7:18  txqueuelen 1000  (Ethernet)
        RX packets 8978  bytes 2314999 (2.2 MiB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 4953  bytes 3720154 (3.5 MiB)
        TX errors 0  dropped 36 overruns 0  carrier 0  collisions 0
"""

MOCK_IFCONFIG_ETH0_DATA = """eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.1.184  netmask 255.255.255.0  broadcast 192.168.1.255
        inet6 2600:1700:cf1:2ae0::15  prefixlen 128  scopeid 0x0<global>
        inet6 fe80::9235:474f:ef56:6c79  prefixlen 64  scopeid 0x20<link>
        inet6 2600:1700:cf1:2ae0:4041:d283:75e6:d00f  prefixlen 64  scopeid 0x0<global>
        ether b8:27:eb:c1:f2:4d  txqueuelen 1000  (Ethernet)
        RX packets 6406806  bytes 959494955 (915.0 MiB)
        RX errors 0  dropped 12150  overruns 0  frame 0
        TX packets 2922800  bytes 3343475400 (3.1 GiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
"""

MOCK_IFCONFIG_DATA = MOCK_IFCONFIG_WLAN0_DATA + "\n\n" + MOCK_IFCONFIG_ETH0_DATA

MOCK_DEVICE_DATA = {
    "last_update": "06/27/2025 17:01:05",
    "bus": 1,
    "address": 0x76,
    "temperature": 31.2,
    "temperature_units": f"{chr(176)}C",
    "pressure": 1019.2,
    "pressure_units": "mbar",
    "humidity": 89.4,
    "humidity_units": "%",
}

MOCK_PYPROJECT_DATA = b'version = "v0.1.2"'

# MOCK_OPEN_CPUINFO_DATA = mock_open(
#        read_data=MOCK_CPUINFO_DATA
#        ).return_value
# MOCK_OPEN_OSRELEASE_DATA = mock_open(
#        read_data=MOCK_OSRELEASE_DATA
#        ).return_value
# MOCK_OPEN_SYS_CLASS_THERMAL_DATA = mock_open(
#        read_data=MOCK_SYS_CLASS_THERMAL_THERMAL_ZONE0_TEMP
#        ).return_value
# MOCK_OPEN_PYPROJECT_DATA = mock_open(
#        read_data=MOCK_PYPROJECT_DATA
#        ).return_value

# def mock_open_side_effect(file, *args, **kwargs):
#    fname = Path(file_name).name
#
#    mocks = {
#            ".config.yaml": lambda: mock_open(read_data=CONFIG_DATA)(),
#            ".secrets.yaml": lambda: mock_open(read_data=SECRETS_DATA)(),
#            "pyproject.toml": lambda: mock_open(read_data=TOML_DATA)(),
#    }
#
#    try:
#        return mocks[fname]()  # call the mock to get file handle
#    except KeyError:
#        raise FileNotFoundError(f"File not found: {file_name}")

# MOCKED_OPEN = MagicMock(side_effect=mock_open_side_effect)

MOCK_SUBPROCESS_CHECK_OUTPUT_SIDE_EFFECT = [
    MOCK_IFCONFIG_ETH0_DATA.encode("utf-8"),
    MOCK_IFCONFIG_WLAN0_DATA.encode("utf-8"),
]

MOCK_CONFIG_DATA = """
---
title: Bosch BME280
subtitle: Temperature, Pressure, Humidity Sensors
logging:
  level: ERROR
web:
  address: 0.0.0.0
  port: 8088
mqtt:
  broker: hastings.attlocal.net
  port: 1883
  username: mqttuser
  password: mqttuser-password
  polling_interval: 1
  qos: 0  
  disable_retain: false 
  auto_discover: true
  expire_after: 119  
bme280:
  address: 0x76
  port: 1
  sensor_name: tph280
  polling_interval: 60
"""

MOCK_OSRELEASE_DATA = """
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
NAME="Debian GNU/Linux"
VERSION_ID="12"
VERSION="12 (bookworm)"
VERSION_CODENAME=bookworm
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
"""

MOCK_LOGGING_CONFIG_DATA = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] - %(levelname)s in %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "wsgi": {
            "class": "logging.StreamHandler",
            "stream": "ext://flask.logging.wsgi_errors_stream",
            "formatter": "default",
        },
    },
    "root": {
        "level": "WARNING",
        "handlers": ["wsgi"],
    },
    "loggers": {
        "mqtt_client": {
            "level": "WARNING",
            "handlers": ["wsgi"],
            "propagate": False,
        },
        "web_server": {
            "level": "DEBUG",
            "handlers": ["wsgi"],
            "propagate": False,
        },
        "example.pi_bme280": {
            "level": "ERROR",
            "handlers": ["wsgi"],
            "propagate": False,
        },
        "paho.mqtt.client": {
            "level": "ERROR",
            "handlers": ["wsgi"],
            "propagate": False,
        },
        "flask.app": {
            "level": "ERROR",
            "handlers": ["wsgi"],
            "propagate": False,
        },
        "werkzeug": {
            "level": "ERROR",
            "handlers": ["wsgi"],
            "propagate": False,
        },
    },
}

MOCK_CPUINFO_DATA ="""processor	: 0
BogoMIPS	: 38.40
Features	: fp asimd evtstrm crc32 cpuid
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd03
CPU revision	: 4

processor	: 1
BogoMIPS	: 38.40
Features	: fp asimd evtstrm crc32 cpuid
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd03
CPU revision	: 4

processor	: 2
BogoMIPS	: 38.40
Features	: fp asimd evtstrm crc32 cpuid
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd03
CPU revision	: 4

processor	: 3
BogoMIPS	: 38.40
Features	: fp asimd evtstrm crc32 cpuid
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd03
CPU revision	: 4

Revision	: a22082
Serial		: 000000009ec1f24d
Model		: Raspberry Pi 3 Model B Rev 1.2
"""
