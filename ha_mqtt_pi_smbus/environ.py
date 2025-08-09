import logging
import subprocess
from typing import Any, Dict

DEGREE = chr(176)


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
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as file_object:
        return float(file_object.read()) / 1000.0


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
    try:
        output = subprocess.check_output(["ifconfig", interface]).decode("utf-8")
        for line in output.splitlines():
            if "ether" in line:
                mac_address = line.split()[1]
                return mac_address
    except subprocess.CalledProcessError:
        return None


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
    with open("/proc/cpuinfo", "r") as f:
        content = f.read()
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
    with open("/etc/os-release", "r") as f:
        content = f.read()
    for line in content.split("\n"):
        token = line.split("=")
        if len(token) == 2:
            name = token[0].strip()
            value = token[1].strip().strip('"')
            info[name] = value
    return info


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
    try:
        return subprocess.check_output(["uptime", "-p"]).decode("utf-8")
    except subprocess.CalledProcessError:   # pragma: no cover
        return None                         # pragma: no cover


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
    try:
        return subprocess.check_output(["uptime", "-s"]).decode("utf-8")
    except subprocess.CalledProcessError:   # pragma: no cover
        return None                         # pragma: no cover
