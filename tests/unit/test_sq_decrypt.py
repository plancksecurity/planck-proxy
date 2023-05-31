import pytest
from proxy.utils.cryptography import decryptusingsq


def test_decryptusingsq_handles_missing_pgp_message():
    # Test that decryptusingsq returns an error message when no PGP message is found in the input
    result = decryptusingsq("This is a plain text message", "my_secret_key.pgp")
    assert isinstance(result, str)
    assert "No -----BEGIN PGP MESSAGE----- found" in result


@pytest.mark.parametrize("collect_email", ["basic.enc.eml"], indirect=True)
def test_sq_decrypt(collect_email, extra_keypair, test_dirs):
    key_path = test_dirs["keys"] / str(extra_keypair.fpr + ".sec.asc")
    assert key_path.exists()
    dec_msg = decryptusingsq(collect_email.decode("utf-8"), str(key_path))
    assert len(dec_msg) == 2
    assert isinstance(dec_msg[0], str)
    assert isinstance(dec_msg[1], list)
    assert "Hello" in dec_msg[0]
    assert extra_keypair.fpr in dec_msg[1]
