from __future__ import annotations

from enum import Enum
import logging
from typing import Any

from paho.mqtt.reasoncodes import ReasonCode


class StateErrorEnum(Enum):
    SUCCESS = (0, None)
    CONNECTED_INCONSISTENT_1 = (
        1,
        "json_state.connected != client.is_connected or "
        + "json_state.connected != client.state.connected",
    )
    CONNECTED_INCONSISTENT_2 = (2, "client.state.connected != client.is_connected")
    DISCOVERED_INCONSISTENT = (3, "json_state.discovered != client.state.discovered")
    NOT_CONNECTED = (
        4,
        "client.state cannot be discovered unless client.state is connected",
    )

    def __new__(cls, code, value):
        """Construct new enum member

        Parameters
        ----------
        code : int
            the ordinal number of the enum member
        value : str
            the value of the enum member

        """
        # Create a new enum instance
        obj = object.__new__(cls)
        # Assign the first value as the canonical value
        obj.code = code
        # Assign the second value as an additional attribute
        obj._value_ = value
        # Map the secondary value to the enum member for lookup
        cls._value2member_map_[value] = obj
        return obj


class State:
    """A class used to cotain the state of the MQTT client

    Attributes
    ----------
    connected:bool
        a boolean indicating whether the client is connected to the MQTT broker
    discovered:bool
        a boolean indicting whether the device sensors are in a discovered state
    rc:int
        the return code from the MQTT client
    error:List[str]
        the list of error messages
    """

    connected: bool = False
    discovered: bool = False
    rc: Any = None
    error_code: list(int) = []
    error: list(str) = []

    def __init__(self, obj: dict = None):
        self.__logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.obj = obj
        if obj is None:
            return
        if "Connected" in obj and obj["Connected"] is not None:
            self.connected = obj["Connected"]
        if "Discovered" in obj and obj["Discovered"] is not None:
            self.discovered = obj["Discovered"]
        if "rc" in obj and obj["rc"] is not None:
            self.rc = obj["rc"]
        if "Errorcode" in obj and obj["Errorcode"] is not None:
            self.error_code = obj["Errorcode"]
        if "Error" in obj and obj["Error"] is not None:
            self.error = obj["Error"]

    def add_error_code(self, error_code):
        """Add error_code to the error_code list

        Parameters
        ----------
        error_code : str
            the error code to add to the list of erroro_code.
        """
        if error_code is not None:
            if error_code not in self.error_code:
                self.error_code.append(error_code)

    def translate_error_codes(self):
        """Translate the error codes to StateErrorEnum's in the error
        list

        Parameters
        ----------
        None
        """
        for error_code in self.error_code:
            self.error.append(StateErrorEnum(error_code).value)

    def validate(self, json_data, is_connected):
        """Validate that the status in the json_data is xonsistent
        with the provided connected state.

        Parameters
        ----------
        json_data : State
            The current MQTT State.
        is_connected : bool
            The current connection state

        Return
        ------
        State : a new state that is corrected to match the connection state
        """
        route = "validate_state"
        new_state = State(self.to_dict())
        if new_state is not None:
            new_state = State(json_data)
        new_state.error_code = []
        new_state.error = []
        new_state.rc = 0
        connected = self.connected
        if new_state.connected != self.connected or new_state.connected != is_connected:
            new_state.add_error_code(StateErrorEnum.CONNECTED_INCONSISTENT_1)
            if new_state.connected != is_connected:
                new_state.connected = is_connected
        if connected != is_connected:
            new_state.add_error_code(StateErrorEnum.CONNECTED_INCONSISTENT_2)
            new_state.connected = is_connected
        if new_state.discovered != self.discovered:
            new_state.add_error_code(StateErrorEnum.DISCOVERED_INCONSISTENT)
            new_state.discovered = self.discovered
        if self.discovered and not is_connected:
            new_state.add_error_code(StateErrorEnum.NOT_CONNECTED)
            new_state.discovered = False
        return new_state

    def to_dict(self):
        """Translate the MQTT State to a dict

        Parameters
        ----------
        None

        Return
        ------
        dict : the value of the MQTT state of the object as a dict
        """
        if not isinstance(self.error, list):
            self.__logger.exception("self.error is str (%s)" % (type(self.error)))
        if self.rc is not None and not isinstance(self.rc, ReasonCode):
            self.__logger.exception("self.rc not ReasonCode (%s)" % (type(self.rc)))
            self.__logger.exception("self.rc (%s)" % (self.rc))
        return {
            "Connected": self.connected,
            "Discovered": self.discovered,
            "rc": self.rc.json() if isinstance(self.rc, ReasonCode) else self.rc,
            "Errorcode": self.error_code,
            "Error": self.error,
        }
