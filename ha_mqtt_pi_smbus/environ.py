import importlib
import logging
import pathlib
import re
import subprocess
import tomllib
from typing import Any, Dict

DEGREE = chr(176)


def readfile(file_name) -> str:
    with open(file_name, "r") as file_object:
        return file_object.read()


def get_command_data(args: list[str]) -> str:
    try:
        return subprocess.check_output(args).decode("utf-8")
    except subprocess.CalledProcessError:
        return None


def getCpuInfo() -> Dict[str, Any]:
    """get Raspberry Pi CPU info

        Parameters
        ----------
        None

        Returns
        -------
        a dict value representing the information read from /proc/cpuinfo

        Example
        ------
        >>> from environ import getCpuInfo
        >>> print(f'The cpu info is as follows:\n{getCpuInfo()}')
       The cpu info is as follows:
    {'cpu': {'Revision': 'a22082', 'Serial': '000000009ec1f24d',
    'Model': 'Raspberry Pi 3 Model B Rev 1.2', 'processors': 4},
    'processors': {'0': {'BogoMIPS': 38.4,x
    'Features':['fp', 'asimd', 'evtstrm', 'crc32', 'cpuid'],
    'CPU implementer': '0x41', 'CPU architecture': 8,
    'CPU variant': '0x0', 'CPU part': '0xd03', 'CPU revision': 4},
    '1': {'BogoMIPS': 38.4,
    'Features': ['fp', 'asimd', 'evtstrm', 'crc32', 'cpuid'],
    'CPU implementer': '0x41', 'CPU architecture': 8, 'CPU variant': '0x0',
    'CPU part': '0xd03', 'CPU revision': 4},
    '2': {'BogoMIPS': 38.4,
    'Features': ['fp', 'asimd', 'evtstrm', 'crc32', 'cpuid'],
    'CPU implementer': '0x41', 'CPU architecture': 8,
    'CPU variant': '0x0', 'CPU part': '0xd03', 'CPU revision': 4},
    '3': {'BogoMIPS': 38.4,
    'Features': ['fp', 'asimd', 'evtstrm', 'crc32', 'cpuid'],
    'CPU implementer': '0x41', 'CPU architecture': 8,
    'CPU variant': '0x0', 'CPU part': '0xd03', 'CPU revision': 4}}}
        >>>
    """
    info = {}
    content = readfile("/proc/cpuinfo")
    groups = content.split("\n\n")
    processors = {}
    for group in groups:
        piece = group.split("\n")
        stanza = {}
        for line in piece:
            if len(line.strip()) > 0:
                token = line.strip().split(":")
                token[0] = token[0].strip()
                token[1] = token[1].strip()
                stanza[token[0]] = token[1]
        processor = stanza.pop("processor", None)
        if processor is not None:
            stanza["BogoMIPS"] = float(stanza["BogoMIPS"])
            stanza["CPU architecture"] = int(stanza["CPU architecture"])
            stanza["CPU revision"] = int(stanza["CPU revision"])
            stanza["Features"] = stanza["Features"].split(" ")
            processors[processor] = stanza
        else:
            stanza["processors"] = len(processors)
            info["cpu"] = stanza
    info["processors"] = processors
    return info


def getTemperature() -> float:
    """get Raspberry Pi CPU temperature in Centigrade as a float

    Parameters
    ----------
    None

    Returns
    -------
    a float value representing the temperature of the Raspberry Pi
    CPU

    Example
    ------
    >>> from environ import getTemperature
    >>> print(f'The temperature of the Raspberry Pi is {getTemperature()}{chr(176)}C')
    The temperature of the Raspberry Pi is 50.464°C
    >>>
    """
    return float(readfile("/sys/class/thermal/thermal_zone0/temp")) / 1000.0


def getOSInfo() -> Dict[str, Any]:
    """get Raspberry Pi OS operating system release information

    Parameters
    ----------
    None

    Returns
    -------
    a dict containing the information retrieved from /etc/os-release

    Example
    ------
    >>> from environ import getOSInfo
    >>> print(f'The OS release information is:\n{getOSInfo()}')
    The OS release information is:
    {'PRETTY_NAME': '"Debian GNU/Linux 12 (bookworm)"',
    'NAME': '"Debian GNU/Linux"', 'VERSION_ID': '"12"',
    VERSION': '"12 (bookworm)"', 'VERSION_CODENAME': 'bookworm',
    'ID': 'debian', 'HOME_URL': '"https://www.debian.org/"',
    'SUPPORT_URL': '"https://www.debian.org/support"',
    'BUG_REPORT_URL': '"https://bugs.debian.org/"'}
    >>>
    """
    info = {}
    content = readfile("/etc/os-release")
    for line in content.split("\n"):
        token = line.split("=")
        if len(token) == 2:
            name = token[0].strip()
            value = token[1].strip().strip('"')
            info[name] = value
    return info


def getMacAddressByInterface(interface) -> str:
    """get the Mac address of the specified interface

    Parameters
    ----------
    interface : str
        a str containing the name of the interface

    Returns
    -------
    a str containing 6 pairs of hexadecimal digits separated by
    semicolongs (:) which is the encoding of the 48-bit mac address of
    the specified interface

    Example
    ------
    >>> from environ import getTemperature
    >>> print(f'The Mac address for wlan0 is {getMacAddressByInterface("wlan0")}')
    The Mac address for wlan0 is b8:27:eb:94:a7:18
    >>>
    """
    output = get_command_data(["ifconfig", interface])
    if output is None:
        return None
    for line in output.splitlines():
        if "ether" in line:
            mac_address = line.split()[1]
            return mac_address


def getMacAddress() -> str:
    """get the 'primary' iac address of the Raspberry pi

    The Mac address for eth0 is returned, if no eth0, then for wlan0,
    if no wlan0, then None is returned

    Parameters
    ----------
    None

    Returns
    -------
    a str containing 6 pairs of hexadecimal digits separated by
    semicolongs (:) which is the encoding of the 48-bit mac address
    of the 'primary' interface or None if the 'primary' interface
    cannot be determined

    Example
    ------
    >>> from environ import getMacAddress
    >>> print(f'The mac address for the primary interface is {getMacAddress()}')
    The mac address for the primary interface is b8:27:eb:c1:f2:4d
    >>>
    """
    mac = getMacAddressByInterface("eth0")
    if mac is not None:
        return mac
    return getMacAddressByInterface("wlan0")


def getObjectId() -> str:
    """get a unique object id representing the Raspberry Pi system

    The object id returned is a str containing the Mac Address for the
    'primary' interface with the semicolons(:) removed. If no 'primary'
    interface can be determined, None is returned.

    Parameters
    ----------
    None

    Returns
    -------
    a str containing 6 pairs of hexadecimal digits which is the encoding
    of the 48-bit mac address of the 'primary' interface or None if the
    'primary' interface cannot be determined

    Example
    ------
    >>> from environ import getObjectId
    >>> print(f'The object id is {getObjectId()}')
    The object id is b827ebc1f24d
    >>>
    """
    return getMacAddress().replace(":", "")


def getUptime() -> str:
    """get the time since the system was rebooted

    Parameters - none

    Returns
    -------
    a str containing the time since the system was rebooted

    Example
    ------
    >>> from environ import getUptime
    >>> print(f'The uptime is {getUptime("")}')
    The Mac address for wlan0 is b8:27:eb:94:a7:18
    >>>
    """
    return get_command_data(["uptime", "-p"])


def getLastRestart() -> str:
    """get the Mac address of the specified interface

    Parameters
    ----------
    none

    Returns
    -------
    a str the date and time of the last reboot

    Example
    ------
    >>> from environ import getTemperature
    >>> print(f'The last restart time is {getLastRestart()}')
    The Mac address for wlan0 is b8:27:eb:94:a7:18
    >>>
    """
    return get_command_data(["uptime", "-s"])


def _get_pyproject_version():
    # Try pyproject first in dev
    pyproject_file = pathlib.Path("pyproject.toml")
    if pyproject_file.exists():
        pyproject = tomllib.loads(readfile(pyproject_file))
        if "version" in pyproject:
            return pyproject["version"]
    return None


def _get_setuptools_version():
    # Try setuptools
    return get_command_data(["python3", "-m", "setuptools_scm"])


def _get_metadata_version():
    # Then try installed metadata
    try:
        return importlib.metadata.version("yourpackage")
    except importlib.metadata.PackageNotFoundError:
        return None


def _get_package_version():
    # Fallback to __version__
    try:
        from . import __version__

        return __version__
    except ImportError:
        return None


def get_version():
    version = _get_pyproject_version()
    if version is not None:
        return version
    version = _get_setuptools_version()
    if version is not None:
        return version
    version = _get_metadata_version()
    if version is not None:
        return version
    version = _get_package_version()
    if version is not None:
        return version
    return "0.0.0-dev"
