import json
from json.decoder import JSONDecodeError
import logging
import logging.config

import flask.logging

def loggerConfig() -> str:
    """ logging configuration

    Parameters
    ----------

    logginglevel : int

        The levels are:
            50 : CRITICAL
            50 : FATAL
            40 : ERROR
            30 : WARN
            20 : INFO
            10 : DEBUG
            0 : NOTSET # logs all levels

    """

    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] - %(levelname)s in %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default',
            },
        },
        'root': {
            'level': 'WARNING',
            'handlers': ['wsgi'],
        },
        'loggers': {
            'mqtt_client': {
                'level': 'WARNING',
                'handlers': ['wsgi'],
                'propagate': False,
            },
            'web_server': {
                'level': 'DEBUG',
                'handlers': ['wsgi'],
                'propagate': False,
            },
            'example.pi_bme280': {
                'level': 'ERROR',
                'handlers': ['wsgi'],
                'propagate': False,
            },
            'paho.mqtt.client': {
                'level': 'ERROR',
                'handlers': ['wsgi'],
                'propagate': False,
            },
            'flask.app': {
                'level': 'ERROR',
                'handlers': ['wsgi'],
                'propagate': False,
            },
            'werkzeug': {
                'level': 'ERROR',
                'handlers': ['wsgi'],
                'propagate': False,
            },
        },
    }

    try:
        with open('logging.config', 'r') as config_file:
            logging_config = json.load(config_file) # For JSON
            # config = yaml.safe_load(f) # For YAML
        if not 'disable_existing_loggers' in logging_config:
            logging_config['disable_existing_loggers'] = False
    except FileNotFoundError as e:
        print('FileNotFoundError')
        logging_config = LOGGING_CONFIG
    except JSONDecodeError as e:
        print(f'\tJSONDecodeError, lineno: {e.lineno}, colno: {e.colno}\n\t{e.msg}')
        logging_config = LOGGING_CONFIG
    except Exception as e:
        print(f'\t{e.__class__}\n\t{e}')
        logging_config = LOGGING_CONFIG
    
    # Apply the logging config
    logging.config.dictConfig(logging_config)
    return logging_config
