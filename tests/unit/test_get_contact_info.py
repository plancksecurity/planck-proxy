import pytest

from email.message import Message
from proxy.utils.parsers import get_contact_info, get_mail_headers


@pytest.mark.parametrize(
    "collect_email, expected",
    [
        ("basic.eml", ("alice@pep.security", "bob@pep.security")),
        (
            "multi_headers.eml",
            ("service@planck-security.net", "andy@planck-security.net"),
        ),
    ],
    indirect=["collect_email"],
)
def test_get_contact_pass(collect_email, expected):
    email = collect_email.decode()
    assert get_contact_info(email) == expected


@pytest.mark.parametrize(
    "collect_email", ["missing_delivered_header.eml"], indirect=True
)
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
    "collect_email, expected",
    [
        ("basic.eml", ("alice@pep.security", "myrecipient@test.com")),
        (
            "missing_delivered_header.eml",
            ("support@planck-security.net", "myrecipient@test.com"),
        ),
    ],
    indirect=["collect_email"],
)
def test_get_recipients(set_settings, collect_email, expected):
    """
    We use the recipient in the settings ignoring the to or delivered-to
    """
    email = collect_email.decode()
    settings = set_settings
    settings["recipient"] = "myrecipient@test.com"
    assert get_contact_info(email) == expected
    settings["recipient"] = False


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
def test_get_mail_headers(inmsg, headername, expected_output):
    assert (
        get_mail_headers(inmsg, headername) == expected_output
        if expected_output is False
        else get_mail_headers(inmsg, headername) == expected_output
    )


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
