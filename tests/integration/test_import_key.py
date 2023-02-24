import subprocess
import sqlite3
import os
import pytest
from pEphelpers import get_contact_info

@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_import_extra_key(settings, test_dirs, collect_email, extra_keypair, cmd_env):
    test_key_fpr = extra_keypair.fpr
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)

    # Run the command
    p = subprocess.run(['./pEpgate decrypt'], shell=True,
            capture_output=True, input=collect_email, env=cmd_env)

    # Check that the key is in the pEp Database
    keys_db = test_dirs['work'] / test_email_to / '.pEp' / 'keys.db'
    db = sqlite3.connect(keys_db)
    keys = db.execute("SELECT primary_key FROM keys")
    assert test_key_fpr in [key[0] for key in keys]

