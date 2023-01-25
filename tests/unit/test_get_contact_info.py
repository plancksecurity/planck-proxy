import pytest
import glob
from pEphelpers import get_contact_info


@pytest.mark.parametrize("test_email, expected",
    [
        ("01", ("andy@pep.security", "andy@0x3d.lu")),
        ("02", ("andy@0x3d.lu", "aw@gate.pep.security")),
        # ("06", ("support@pep-security.net", ["aw@pep.security", "foo@0x3d.lu", "bla@0x3d.lu"])), TODO: This fails!
    ])
def test_get_contact_pass(test_email, expected):
    email = glob.glob('emails/' + test_email + '*')[0]
    with open(email) as f:
        assert get_contact_info(f.read()) == expected

