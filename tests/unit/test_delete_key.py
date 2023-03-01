import subprocess
import sqlite3
import os
import pytest
from pEphelpers import get_contact_info


# ## W O R K   I N    P R O G R E S S

@pytest.mark.parametrize('collect_email', ["basic_keyreset.eml"], indirect=True)
def test_import_extra_key(settings, test_dirs, collect_email, extra_keypair):
    test_key_fpr = extra_keypair.fpr
    test_email_from, test_email_to = get_contact_info(collect_email)
    cmd_env = os.environ.copy()
    cmd_env['work_dir'] = test_dirs['work']
    cmd_env['keys_dir'] = test_dirs['keys']
    cmd_env['EXTRA_KEYS'] = extra_keypair.fpr


    # Run the command
    with open(collect_email, 'rb') as email:
        subprocess.run(['./pEpgate decrypt'], shell=True,
            capture_output=True, input=email.read(), env=cmd_env)

    # Check that the key is in the pEp Database
    keys_db = test_dirs['work'] / test_email_to / '.pEp' / 'keys.db'
    db = sqlite3.connect(keys_db)
    keys = db.execute("SELECT primary_key FROM keys")
    assert test_key_fpr not in [key[0] for key in keys]

    #Check that keywords have been deleted from output eml
    processed_mail = test_dirs['work'] / test_email_to / test_email_from / 'keys.db'

    test_settings = {}
    test_settings['test-nomails']  = True
    test_settings['work_dir'] = str(test_dirs['work'])
    test_settings['keys_dir'] = str(test_dirs['keys'])
    test_settings['mode']  = 'decrypt'
    test_settings['scan_pipes']  = [{"name": "dummy filter", "cmd": filter_command}]

    command = f'python ./src/scripts/_gate_test_runner.py "{str(test_settings)}"'
    p = subprocess.run([command], shell=True, capture_output=True, input=collect_email)

    assert p.returncode is 0