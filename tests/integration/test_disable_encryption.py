import subprocess
import os
import pytest
from pEphelpers import get_contact_info
from update_settings import override_settings

@pytest.mark.parametrize('collect_email', ["basic_noencrypt.eml"], indirect=True)
def test_encrypt_noencrypt_message_authorized(set_settings, settings_file, test_dirs, collect_email, extra_keypair, bob_key, cmd_env):
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)

    test_settings = {
        "EXTRA_KEYS": ["3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3"],
        "noencrypt_senders":    ["alice@pep.security"],
        "DEBUG": True
    }
    override_settings(test_dirs['tmp'], test_settings)

    command = (f"./pEpgate encrypt --settings_file {settings_file}")
    subprocess.run([command], shell=True,
            capture_output=True, input=collect_email, env=cmd_env)

    decrypt_out_path = test_dirs['work'] / test_email_from / test_email_to
    out_folder = [f.path for f in os.scandir(decrypt_out_path)][0]
    encrypted = out_folder + '/in.encrypt.processed.eml'
    with open(encrypted) as encrypted_email:
        encrypted_data = encrypted_email.read()
    assert "Hello proxy" in encrypted_data
    assert "NOENCRYPT" not in encrypted_data

# @pytest.mark.parametrize('collect_email', ["basic_noencrypt.eml"], indirect=True)
# def test_encrypt_noencrypt_message_not_authorized(set_settings, settings_file, test_dirs, collect_email, extra_keypair, bob_key, cmd_env):
#     email = collect_email.decode()
#     test_email_from, test_email_to = get_contact_info(email)

#     test_settings = {
#         "EXTRA_KEYS": ["3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3"],
#         "noencrypt_senders":    ["None"],
#         "work_dir": "/Users/alice/Projects/pEpGate/temp_work_dir"
#     }
#     override_settings(test_dirs['tmp'], test_settings)

#     command = (f"./pEpgate encrypt --settings_file {settings_file}")
#     p = subprocess.run([command], shell=True,
#             capture_output=True, input=collect_email, env=cmd_env)

#     decrypt_out_path = test_dirs['work'] / test_email_from / test_email_to
#     out_folder = [f.path for f in os.scandir(decrypt_out_path)][0]
#     encrypted = out_folder + '/in.encrypt.processed.eml'
#     with open(encrypted) as encrypted_email:
#         encrypted_data = encrypted_email.read()
#     assert "Hello proxy" not in encrypted_data
