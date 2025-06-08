import psutil
import subprocess

class CPUTemperature:
    def getTemperature():
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file_object:
            return float(file_object.read()) / 1000.0

class MacAddress:
    def getByInterface(interface) -> str:
        try:
            output = subprocess.check_output(["ifconfig", interface]).decode("utf-8")
            for line in output.splitlines():
                if "ether" in line:
                    mac_address = line.split()[1]
                    return mac_address
        except subprocess.CalledProcessError:
            return None

    def get() -> str:
        mac = MacAddress.getByInterface("eth0")
        if not mac is None:
            return mac
        return MacAddress.getByInterface("wlan0")

    def getObjectId() -> str:
        return MacAddress.get().replace(":","")

class CpuInfo:
    def __init__(self):
        self.info = {}
        with open('/proc/cpuinfo','r') as f:
            content = f.read()
        groups = content.split("\n\n")
        stanzas = []
        processors = {}
        for group in groups:
            piece = group.split("\n")
            stanza = {}
            for line in piece:
                if len(line) > 0:
                    token = line.split(":")
                    token[0] = token[0].strip()
                    token[1] = token[1].strip()
                    stanza[token[0]] = token[1]
            processor = stanza.pop('processor', None)
            if not processor is None:
                stanza['BogoMIPS'] = float(stanza['BogoMIPS'])
                stanza['CPU architecture'] = int(stanza['CPU architecture'])
                stanza['CPU revision'] = int(stanza['CPU revision'])
                stanza['Features'] = stanza['Features'].split(' ')
                processors[processor] = stanza
            else:
                stanza['processors'] = len(processors)
                self.info['cpu'] = stanza
        self.info['processors'] = processors

class OSInfo:
    def __init__(self):
        self.info = {}
        with open('/etc/os-release','r') as f:
            content = f.read()
        for line in content.split("\n"):
            token = line.split("=")
            if len(token) == 2:
                self.info[token[0].strip()] = token[1].strip()

class NetIfAddr:
    def __init__(self):
        ifaces = psutil.net_if_addrs()
        if 'eth0' in ifaces:
            iface = ifaces['eth0']
        elif 'wlan0' in ifaces:
            iface = ifaces['wlan0']
        else:
            iface = None
        if not iface is None:
            for ifc in iface:
                self.address = ifc.address
                return
        self.address = None    
