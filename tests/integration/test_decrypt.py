import subprocess
import shutil
import sqlite3
import os
import pytest
import sys
import compare_mails
from pEphelpers import get_contact_info
from pathlib import Path
from compare_mails import get_email_body
from override_settings import override_settings


@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_import_extra_key(set_settings, settings_file, test_dirs, collect_email, extra_keypair, cmd_env):
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)

    test_settings = {
        "EXTRA_KEYS": [extra_keypair.fpr],
    }
    override_settings(settings_file, test_settings)

    # Run the command
    command = (f"./pEpgate decrypt --settings_file {settings_file}")
    subprocess.run([command], shell=True, capture_output=True,
                   input=collect_email, env=cmd_env)

    # Check that the key is in the pEp Database
    keys_db = test_dirs['work'] / test_email_to / '.pEp' / 'keys.db'
    db = sqlite3.connect(keys_db)
    keys = db.execute("SELECT primary_key FROM keys")
    assert extra_keypair.fpr in [key[0] for key in keys]


@pytest.mark.parametrize('collect_email', ["basic.noextra.enc.eml"], indirect=True)
def test_decrypt_message_no_key(set_settings, settings_file, collect_email, test_dirs, extra_keypair, cmd_env):
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)

    test_settings = {
        "EXTRA_KEYS": [extra_keypair.fpr],
        "DEBUG": True
    }
    override_settings(settings_file, test_settings)

    command = (f"./pEpgate decrypt --settings_file {settings_file}")
    subprocess.run([command], shell=True,
                   capture_output=True, input=collect_email, env=cmd_env)

    decrypt_out_path = test_dirs['work'] / test_email_to / test_email_from
    out_folder = [f.path for f in os.scandir(decrypt_out_path)][0]
    decrypted = out_folder + '/in.decrypt.processed.eml'
    with open(decrypted) as decrypted_email:
        decrypted_data = decrypted_email.read()

    assert get_email_body(collect_email.decode()
                          ) == get_email_body(decrypted_data)


@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_decrypt_message(set_settings, settings_file, test_dirs, collect_email, extra_keypair, cmd_env):
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)

    test_settings = {
        "EXTRA_KEYS": [extra_keypair.fpr],
        "DEBUG": True
    }
    override_settings(settings_file, test_settings)

    command = (f"./pEpgate decrypt --settings_file {settings_file}")
    subprocess.run([command], shell=True,
                   capture_output=True, input=collect_email, env=cmd_env)

    decrypt_out_path = test_dirs['work'] / test_email_to / test_email_from
    out_folder = [f.path for f in os.scandir(decrypt_out_path)][0]
    decrypted = out_folder + '/in.decrypt.processed.eml'
    with open(decrypted) as decrypted_email:
        decrypted_data = decrypted_email.read()
    assert "Hello encrypted world!" in decrypted_data
