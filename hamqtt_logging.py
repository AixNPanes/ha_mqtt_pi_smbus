import logging
import flask.logging

def loggerConfig(logginglevel):
    logging.basicConfig(
        level=logginglevel,
        format='[%(asctime)s] - %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(flask.logging.wsgi_errors_stream)]
    )
