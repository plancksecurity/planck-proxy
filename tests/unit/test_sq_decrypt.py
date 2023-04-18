import pytest
from src.pEphelpers import decryptusingsq


def test_decryptusingsq_handles_missing_pgp_message():
    # Test that decryptusingsq returns an error message when no PGP message is found in the input
    result = decryptusingsq("This is a plain text message", "my_secret_key.pgp")
    assert isinstance(result, str)
    assert "No -----BEGIN PGP MESSAGE----- found" in result


@pytest.mark.parametrize("collect_email", ["basic.enc.eml"], indirect=True)
def test_sq_decrypt(collect_email, extra_keypair, test_dirs):
    key_path = test_dirs["keys"] / str(extra_keypair.fpr + ".sec.asc")
    dec_msg = decryptusingsq(str(collect_email), str(key_path))
    assert len(dec_msg) == 2
    assert isinstance(dec_msg[0], str)
    assert isinstance(dec_msg[1], list)
