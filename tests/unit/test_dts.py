import pytest

from proxy.proxy_main import enable_dts
from proxy.utils.message import Message
from proxy.proxy_settings import settings


@pytest.mark.parametrize("collect_email", ["basic_dts.eml"], indirect=True)
def test_dts(set_settings, collect_email):
    global settings
    settings["mode"] = "decrypt"
    settings["dts_domains"] = ["icandts.org"]
    settings["work_dir"] = "work"

    message = Message()
    message.inmail = collect_email.decode()
    enable_dts(message)

    assert settings["dts"] == "dtsaddress@icandts.org"


@pytest.mark.parametrize("collect_email", ["basic.eml"], indirect=True)
def test_dts_no_header(set_settings, collect_email):
    global settings
    settings["mode"] = "decrypt"
    settings["dts_domains"] = ["icandts.org"]
    settings["work_dir"] = "work"

    message = Message()
    message.inmail = collect_email.decode()
    enable_dts(message)

    assert settings["dts"] is None


@pytest.mark.parametrize("collect_email", ["basic_dts.eml"], indirect=True)
def test_dts_unallowed_domain(set_settings, collect_email):
    global settings
    settings["mode"] = "decrypt"
    settings["dts_domains"] = ["another_dts_domain.org"]
    settings["work_dir"] = "work"

    message = Message()
    message.inmail = collect_email.decode()
    enable_dts(message)

    assert settings["dts"] is None
