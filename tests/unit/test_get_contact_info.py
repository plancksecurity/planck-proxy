import pytest

from helpers import collect_email
from pEphelpers import get_contact_info


@pytest.mark.parametrize("email_finder_expr, expected",
    [
        ("01*", ("andy@pep.security", "andy@0x3d.lu")),
        ("02*", ("andy@0x3d.lu", "aw@gate.pep.security")),
        ("11*", ("service@pep-security.net", "andy@pep-security.net")),
    ])
def test_get_contact_pass(email_finder_expr, expected):
    assert get_contact_info(collect_email(email_finder_expr)) == expected

def test_get_contact_fail():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
            get_contact_info(collect_email("06*"))
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 3

