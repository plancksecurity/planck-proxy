import pytest
import json
import os
import tempfile

from email.message import Message
from src.pEphelpers import get_contact_info, getmailheaders, jsonlookup


@pytest.mark.parametrize(
    "collect_email, expected",
    [
        ("01*", ("andy@pep.security", "andy@0x3d.lu")),
        ("02*", ("andy@0x3d.lu", "aw@gate.pep.security")),
        ("11*", ("service@pep-security.net", "andy@pep-security.net")),
    ],
    indirect=["collect_email"],
)
def test_get_contact_pass(collect_email, expected):
    email = collect_email.decode()
    assert get_contact_info(email) == expected


@pytest.mark.parametrize("collect_email", ["06*"], indirect=True)
def test_get_contact_fail(set_settings, collect_email):
    """
    When we cannot determine who contacted us, ensure that the method fails
    """
    email = collect_email.decode()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        get_contact_info(email)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 3


@pytest.mark.parametrize(
    "inmsg, headername, expected_output",
    [
        (
            "From: sender@example.com\nTo: recipient@example.com\nSubject: Test email\n\nThis is a test email.",
            None,
            [
                {"From": "sender@example.com"},
                {"To": "recipient@example.com"},
                {"Subject": "Test email"},
            ],
        ),
        (
            "From: sender@example.com\nTo: recipient@example.com\nSubject: Test email\n\nThis is a test email.",
            "From",
            ["sender@example.com"],
        ),
        ("No headers email", None, []),
        (["Invalid input"], None, False),
    ],
)
def test_getmailheaders(inmsg, headername, expected_output):
    assert (
        getmailheaders(inmsg, headername) == expected_output
        if expected_output is False
        else getmailheaders(inmsg, headername) == expected_output
    )


@pytest.fixture
def json_map_file():
    data = {
        "colors": ["red", "green", "blue"],
        "fruits": ["apple", "banana", "cherry"],
        "vehicles": ["car", "bike", "boat"],
    }
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        json.dump(data, f)
    yield f.name
    f.close()
    os.unlink(f.name)


@pytest.mark.parametrize(
    "key, expected_output, bidilookup",
    [
        ("colors", ["red", "green", "blue"], False),
        ("fruits", ["apple", "banana", "cherry"], False),
        ("vehicles", ["car", "bike", "boat"], False),
        ("red", None, False),
        ("car", None, False),
        ("apple", None, False),
        ("blue", "colors", True),
        ("bike", "vehicles", True),
        ("cherry", "fruits", True),
    ],
)
def test_jsonlookup(json_map_file, key, expected_output, bidilookup):
    result = jsonlookup(json_map_file, key, bidilookup=bidilookup)
    assert result == expected_output


def test_get_contact_info_sender_only():
    message = Message()
    message["From"] = "sender@example.com"
    message["Delivered-To"] = "recipient@example.com"

    sender, recipient = get_contact_info(message.as_string())
    assert sender == "sender@example.com"
    assert recipient == "recipient@example.com"


def test_get_contact_info_with_return_path():
    message = Message()
    message["Return-Path"] = "<sender@example.com>"
    message["Delivered-To"] = "recipient@example.com"

    sender, recipient = get_contact_info(message.as_string())
    assert sender == "sender@example.com"
    assert recipient == "recipient@example.com"
