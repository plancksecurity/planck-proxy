import subprocess
import sqlite3
import os
import pytest
from pEphelpers import get_contact_info


## W O R K   I N    P R O G R E S S

@pytest.mark.parametrize('collect_email', ["basic_keyreset.eml"], indirect=True)
def test_import_extra_key(settings, test_dirs, collect_email, extra_keypair):
    test_key_fpr = extra_keypair.fpr
    test_email_from, test_email_to = get_contact_info(collect_email)
    cmd_env = os.environ.copy()
    cmd_env['work_dir'] = test_dirs['work']
    cmd_env['keys_dir'] = test_dirs['keys']

    # Run the command
    with open(collect_email, 'rb') as email:
        subprocess.run(['./pEpgate decrypt'], shell=True,
            capture_output=True, input=email.read(), env=cmd_env)

    # Check that the key is in the pEp Database
    keys_db = test_dirs['work'] / test_email_to / '.pEp' / 'keys.db'
    db = sqlite3.connect(keys_db)
    keys = db.execute("SELECT primary_key FROM keys")
    assert test_key_fpr not in [key[0] for key in keys]