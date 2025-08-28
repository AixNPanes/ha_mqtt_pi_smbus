import copy
from importlib.metadata import version, PackageNotFoundError
import importlib
import logging
import pathlib
import re
import socket
import subprocess
import sys
import tomllib
from typing import Any, Dict
import yaml


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    '''Recursively merges two dictionaries.

    Two dict structures will be merged.  Values from dict2 will
    overwrite values from dict1 in case of conflicts, except for
    nested dictionaries, which are recursively merged.

    Parameters
    ----------
    dict1 ; Dict[atr, Any]
    dict2 ; Dict[atr, Any]

    Returns
    -------
    dict

    '''
    if not dict1:
        return dict2 if dict2 else {}
    elif not dict2:
        return dict1

    # Start with a copy to avoid modifying original dict1
    merged_dict: Dict[str, Any] = copy.deepcopy(dict1)

    for key, value in dict2.items():
        if (
            key in merged_dict
            and isinstance(merged_dict[key], dict)
            and isinstance(value, dict)
        ):
            # If both values are dictionaries, recursively merge them
            merged_dict[key] = deep_merge_dicts(merged_dict[key], value)
        else:
            # Otherwise, overwrite the value from dict1 with the value from dict2
            merged_dict[key] = value
    return merged_dict


def read_yaml(file_path) -> Dict[str, Any]:
    '''
    Read yaml from the file specified by file_path
    '''
    logger = logging.getLogger(__name__)
    try:
        data = readfile(file_path)
        return yaml.safe_load(data)
    #        with open(file_path, 'r') as file:
    #            data = yaml.safe_load(file)
    #            return data
    except FileNotFoundError:
        return None
    except yaml.YAMLError as e:
        logger.error('Error parsing YAML: %s', e)
        return None


def auto_int(x) -> int:
    '''
    convert a value to an int
    '''
    return int(x, 0)


def ipaddress(ip: str):
    '''
    convert an ip address to its 32-bit value
    '''
    try:
        return socket.inet_aton(ip)
    except OSError as e:
        print(f'Invalid ipaddress ({ip}): {e}')

def readfile(file_name) -> str:
    '''Read a file

    Parameters
    ----------
    file_name : str
        The name of the file to be read
    '''
    with open(file_name, 'r') as file_object:
        return file_object.read()


def get_command_data(args: list[str]) -> str:
    '''Issue a command to the underlying operating system and return the
    result as a UTF-8 encoded string

    Parameters
    ----------
    args : list[str]
        An array containing the name of the command and the arguments
        to that command as elements of an array

    Return
    ------
    str : A string with the results of the command encoded as UTF-8. None
        if there is an error.
    '''
    try:
        return subprocess.check_output(args).decode('utf-8')
    except subprocess.CalledProcessError:
        return None
