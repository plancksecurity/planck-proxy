import pytest
from pEphelpers import decryptusingsq

@pytest.mark.xfail(reason="UnboundLocalError: local variable 'keyused' referenced before assignment") #FIXME
@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_sq_decrypt(collect_email, extra_keypair, test_dirs):
    key_path = test_dirs['keys'] / str(extra_keypair.fpr + '.sec.asc')
    dec_msg = decryptusingsq(collect_email, str(key_path))
    assert dec_msg is 0
