import subprocess
import os
import pytest
from pEphelpers import get_contact_info


@pytest.mark.parametrize('collect_email', ["basic_noencrypt.eml"], indirect=True)
def test_encrypt_noencrypt_message(settings, test_dirs, collect_email, extra_keypair, bob_key, cmd_env):
    cmd_env['EXTRA_KEYS'] = extra_keypair.fpr
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)
    subprocess.run(['./pEpgate encrypt --DEBUG'], shell=True,
            capture_output=True, input=collect_email, env=cmd_env)

    decrypt_out_path = test_dirs['work'] / test_email_from / test_email_to
    out_folder = [f.path for f in os.scandir(decrypt_out_path)][0]
    encrypted = out_folder + '/in.encrypt.processed.eml'
    with open(encrypted) as encrypted_email:
        encrypted_data = encrypted_email.read()
    assert "Hello proxy" in encrypted_data
    assert "NOENCRYPT" not in encrypted_data

@pytest.mark.parametrize('collect_email', ["basic_noencrypt.eml"], indirect=True)
def test_encrypt_noencrypt_message_no_debug(settings, test_dirs, collect_email, extra_keypair, bob_key, cmd_env):
    cmd_env['EXTRA_KEYS'] = extra_keypair.fpr
    cmd_env['DEBUG'] = 'False'
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)
    p = subprocess.run(['./pEpgate encrypt'], shell=True,
            capture_output=True, input=collect_email, env=cmd_env)

    decrypt_out_path = test_dirs['work'] / test_email_from / test_email_to
    out_folder = [f.path for f in os.scandir(decrypt_out_path)][0]
    encrypted = out_folder + '/in.encrypt.processed.eml'
    with open(encrypted) as encrypted_email:
        encrypted_data = encrypted_email.read()
    assert "Hello proxy" not in encrypted_data
