import pytest
from unittest.mock import Mock
from pEpgatemain import add_routing_and_headers, init_logging

from dataclasses import dataclass


@dataclass
class MockpEpMessage:
    opt_fields: dict = None

    def __str__(self):
        return f"{self.opt_fields}"


@dataclass
class MockpEpId:
    address: str = ""


@pytest.fixture
def pEp():
    pEp = Mock()
    pEp.engine_version = "1.0.0"
    return pEp


def test_add_routing_and_headers(set_settings, pEp, message, test_dirs):
    settings = set_settings
    settings["mode"] = "decrypt"
    settings["work_dir"] = str(test_dirs["work"])

    message.them["addr"] = "user@example.com"
    message.msg["inmail"] = "This is a test message."

    init_logging(message)

    message.msg["dst"] = MockpEpMessage()
    message.msg["dst"].opt_fields = {"Some-Header": "Some-Value"}
    message.us["pepid"] = MockpEpId()
    message.us["pepid"].address = "user@example.com"
    add_routing_and_headers(pEp, message)

    assert "X-pEpGate-mode" in message.msg["dst"]
    assert "X-pEpGate-version" in message.msg["dst"]
    assert "X-pEpEngine-version" in message.msg["dst"]
    assert "X-NextMX" in message.msg["dst"]


def test_add_routing_and_headers_with_nextmx(set_settings, pEp, message, test_dirs):
    settings = set_settings
    settings["mode"] = "decrypt"
    settings["work_dir"] = str(test_dirs["work"])
    settings["home"] = str(test_dirs["root"])
    settings["nextmx_map"] = test_dirs["root"] / "tests_settings" / "nextmx.map"

    message.them["addr"] = "user@example.com"
    message.msg["inmail"] = "This is a test message."
    init_logging(message)

    message.msg["dst"] = MockpEpMessage()
    message.msg["dst"].opt_fields = {"Some-Header": "Some-Value"}
    message.us["pepid"] = MockpEpId()
    message.us["pepid"].address = "user@example.com"

    add_routing_and_headers(pEp, message)

    assert settings["netmx"] == "123.456.789.01:23"
    assert "'X-NextMX': '123.456.789.01:23'" in message.msg["dst"]
