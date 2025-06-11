import logging
import flask.logging

def loggerConfig(logginglevel:int):
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
            0 : NOTSET

    """
    logging.basicConfig(
        level=logginglevel,
        format='[%(asctime)s] - %(levelname)s in %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(flask.logging.wsgi_errors_stream)]
    )
