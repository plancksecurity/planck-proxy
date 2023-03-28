import subprocess
import sqlite3
import os
import pytest
from update_settings import override_settings
from pEphelpers import get_contact_info


@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_import_extra_key(set_settings, settings_file, test_dirs, collect_email, extra_keypair, cmd_env):
    test_key_fpr = extra_keypair.fpr
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)

    test_settings = {
        "EXTRA_KEYS": "3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3",
    }
    override_settings(test_dirs['tmp'], test_settings)

    # Run the command
    command = (f"./pEpgate decrypt --settings_file {settings_file}")
    subprocess.run([command], shell=True, capture_output=True,
                   input=collect_email, env=cmd_env)

    # Check that the key is in the pEp Database
    keys_db = test_dirs['work'] / test_email_to / '.pEp' / 'keys.db'
    db = sqlite3.connect(keys_db)
    keys = db.execute("SELECT primary_key FROM keys")
    assert test_key_fpr in [key[0] for key in keys]
