import pytest
from proxy.proxy_settings import settings
from unittest.mock import patch


class MockIdentity:
    def __init__(self, username, address):
        self.username = username
        self.address = address


def test_create_planck_message(capfd):
    from proxy.proxy_main import create_planck_message
    from proxy.utils.message import Message
    class MockPlanck:
        class Message:
            def __init__(self, inmail):
                self.from_ = MockIdentity("from_username", "from@example.com")
                self.to = [MockIdentity("to_username", "to@example.com")]
                self.cc = []
                self.bcc = []

    mock_message = Message("foo")
    mock_planck = MockPlanck()
    global settings
    settings["mode"] = "decrypt"
    settings["logpath"] = ""
    settings["textlog"] = ""

    create_planck_message(mock_planck, mock_message)
    print(settings["textlog"])
    captured = capfd.readouterr()
    assert "from_username" in captured.out
    assert "from@example.com" in captured.out
    assert "to_username" in captured.out
    assert "to@example.com" in captured.out


def test_create_planck_message_no_username(capfd):
    from proxy.proxy_main import create_planck_message
    from proxy.utils.message import Message
    class MockPlanck:
        class Message:
            def __init__(self, inmail):
                self.from_ = MockIdentity(None, "from@example.com")
                self.to = [MockIdentity("to_username", "to@example.com")]
                self.cc = []
                self.bcc = []

    mock_message = Message("foo")
    mock_planck = MockPlanck()
    global settings
    settings["mode"] = "decrypt"
    settings["logpath"] = ""
    settings["textlog"] = ""

    create_planck_message(mock_planck, mock_message)
    print(settings["textlog"])
    captured = capfd.readouterr()
    assert "from_username" not in captured.out
    assert "from@example.com" in captured.out
    assert "to_username" in captured.out
    assert "to@example.com" in captured.out


def test_create_planck_message_no_email():
    from proxy.proxy_main import create_planck_message
    from proxy.utils.message import Message
    class MockPlanck:
        class Message:
            def __init__(self, inmail):
                self.from_ = MockIdentity("from_username", None)
                self.to = [MockIdentity("to_username", "to@example.com")]
                self.cc = []
                self.bcc = []

    mock_message = Message("foo")
    mock_planck = MockPlanck()
    global settings
    settings["mode"] = "decrypt"
    settings["logpath"] = ""
    settings["textlog"] = ""

    with pytest.raises(SystemExit) as exc_info:
        create_planck_message(mock_planck, mock_message)

    assert exc_info.value.code == 5  # Check if the exit code is 5


if __name__ == "__main__":
    pytest.main()
