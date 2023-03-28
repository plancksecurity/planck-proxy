import subprocess
import os
import pytest
from pEphelpers import get_contact_info
from update_settings import override_settings


@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_decrypt_message_keep(set_settings, settings_file, test_dirs, collect_email, extra_keypair, cmd_env):
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)

    test_settings = {
        "EXTRA_KEYS": "3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3",
        "DEBUG": True
    }
    override_settings(test_dirs['tmp'], test_settings)

    command = (f"./pEpgate decrypt --settings_file {settings_file}")
    subprocess.run([command], shell=True,
                   capture_output=True, input=collect_email, env=cmd_env)

    decrypt_out_path = test_dirs['work'] / test_email_to / test_email_from
    assert os.listdir(decrypt_out_path)


@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_decrypt_message_deletion(set_settings, settings_file, test_dirs, collect_email, extra_keypair, cmd_env):
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)

    test_settings = {
        "EXTRA_KEYS": "3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3",
        "DEBUG": False
    }
    override_settings(test_dirs['tmp'], test_settings)

    command = (f"./pEpgate decrypt --settings_file {settings_file}")
    subprocess.run([command], shell=True,
                   capture_output=True, input=collect_email, env=cmd_env)

    decrypt_out_path = test_dirs['work'] / test_email_to / test_email_from
    assert not os.listdir(decrypt_out_path)
