import logging
import flask.logging

def loggerConfig(logginglevel:int):
    logging.basicConfig(
        level=logginglevel,
        format='[%(asctime)s] - %(levelname)s in %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(flask.logging.wsgi_errors_stream)]
    )
