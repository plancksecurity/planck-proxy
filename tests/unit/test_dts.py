import pytest

from src.proxy_main import enable_dts
from src.utils.message import Message
from proxy_settings import settings


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
