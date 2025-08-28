# tests/test_util.py
import builtins
import logging
# import sys
from pathlib import Path
import subprocess
import sys
# import time
import types
from unittest import TestCase, mock
from unittest.mock import patch, mock_open
import unittest
import yaml

from ha_mqtt_pi_smbus.util import (
    deep_merge_dicts,
    read_yaml,
    auto_int,
    ipaddress,
    readfile,
    get_command_data,
)

CONFIG_DATA = """---
title: title
web:
    address: 1.2.3.4
    port: 1234
mqtt:
    broker: 5.6.7.8
    port: 5678
    username: me
    password: mine
    qos: 1
    disable_retain: False
    auto_discover: True
    expire_after: 99
"""
SECRETS_DATA = """---
title: Title
web:
    address: 5.6.7.8
"""
TOML_DATA = b'version = "v0.1.2"'


def mock_open_side_effect(self, file_name, *args, **kwargs):
    mock_file1 = mock_open(read_data=self.CONFIG_DATA)
    mock_file2 = mock_open(read_data=self.SECRETS_DATA)
    mock_file3 = mock_open(read_data=self.TOML_DATA)
    # Call the mock_open instance to get the file handle
    if Path(file_name).name == ".config.yaml":
        return mock_file1()
    elif Path(file_name).name == "secrets.yaml":
        return mock_file2()
    elif Path(file_name).name == "pyproject.toml":
        return mock_file3()
    else:
        raise FileNotFoundError(f"File not found: {file_name}")


class TestUtil(TestCase):
    def test_deep_merge_dicts(self):
        dict1 = {
            "a": "a",
            "b": "b",
            "c": {
                "d": "d",
                "e": "e",
            },
            "f": {
                "g": "g",
                "h": "h",
                "i": {"j": "j", "k": "k"},
            },
        }
        dict2 = {"f": {"i": {"j": "jj", "l": "ll"}}}
        dict3 = deep_merge_dicts(dict1, dict2)
        dict1["a"] = "1"
        self.assertEqual(len(dict3), 4)
        self.assertEqual(len(dict3["f"]), 3)
        self.assertEqual(len(dict3["f"]["i"]), 3)
        self.assertEqual(dict3["f"]["i"]["j"], "jj")
        self.assertEqual(dict1["a"], "1")
        self.assertEqual(dict3["a"], "a")
        dict3 = deep_merge_dicts(dict1, {})
        self.assertEqual(len(dict3), len(dict1))
        dict3 = deep_merge_dicts({}, dict2)
        self.assertEqual(dict3, {"f": {"i": {"j": "jj", "l": "ll"}}})

    @patch("builtins.open", new_callable=mock_open, read_data="")
    def test_readfile_null(self , mock_file):
        null = readfile("/dev/null")
        self.assertEqual(len(null), 0)

    @patch("builtins.open", new_callable=mock_open, read_data="mock_data")
    def test_readfile_data(self , mock_file):
        data = readfile("mock_data")
        self.assertEqual(data, "mock_data")

    @patch(
        "ha_mqtt_pi_smbus.util.readfile",
        return_value="""---
a:
   b: b
""",
    )
    def test_read_yaml_ok(self, mock_read):
        data = read_yaml(mock_read)
        self.assertEqual(data, {"a": {"b": "b"}})

    @patch("ha_mqtt_pi_smbus.util.read_yaml", side_effect=yaml.YAMLError)
    @patch(
        "ha_mqtt_pi_smbus.util.readfile",
        return_value="""
---
a:a
   b: b
   c: c
""",
    )
    def test_read_yaml_bad_yaml(self, mock_read, mock_read_yaml):
        data = read_yaml(mock_read)
        self.assertEqual(data, None)

    @patch("ha_mqtt_pi_smbus.util.read_yaml", side_effect=FileNotFoundError)
    def test_read_yaml_file_not_found(self, mock_read_yaml):
        data = read_yaml("bad.file")
        self.assertEqual(data, None)

    def test_auto_int(self):
        self.assertEqual(auto_int("0x0a"), 10)
        self.assertEqual(auto_int("0b1010"), 10)
        self.assertEqual(auto_int("0o12"), 10)
        self.assertEqual(auto_int("10"), 10)

    @patch("ha_mqtt_pi_smbus.util.ipaddress", side_effect=OSError)
    def test_ipaddress(self, mock_ipaddress):
        self.assertEqual(ipaddress("127.0.0.1").hex(), "7f000001")
        self.assertEqual(ipaddress("192.168.1.211").hex(), "c0a801d3")
        self.assertEqual(ipaddress("256.168.1.211"), None)
    def test_getcmd_success(self):
        self.assertEqual(get_command_data(["echo", "Hello! World!"]), "Hello! World!\n")

    @patch("subprocess.check_output")
    def test_getcmd_fail(self, mock_check_output):
        mock_check_output.side_effect = subprocess.CalledProcessError(
            returncode=1,  # Non-zero exit status
            cmd="some_command",
            stderr="Error output from command",
        )
        result = get_command_data(["echo", "Hello! World!"])
        self.assertIsNone(result)