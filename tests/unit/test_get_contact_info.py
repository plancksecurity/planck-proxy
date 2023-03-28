import pytest
from pEphelpers import get_contact_info


@pytest.mark.parametrize("collect_email, expected",
                         [
                             ("01*", ("andy@pep.security", "andy@0x3d.lu")),
                             ("02*", ("andy@0x3d.lu", "aw@gate.pep.security")),
                             ("11*", ("service@pep-security.net",
                              "andy@pep-security.net")),
                         ], indirect=["collect_email"])
def test_get_contact_pass(collect_email, expected):
    email = collect_email.decode()
    assert get_contact_info(email) == expected


@pytest.mark.parametrize('collect_email', ["06*"], indirect=True)
def test_get_contact_fail(set_settings, collect_email):
    """
    When we cannot determine who contacted us, ensure that the method fails
    """
    email = collect_email.decode()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        get_contact_info(email)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 3
