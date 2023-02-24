import subprocess
import shutil
import sqlite3
import os
import pytest
from pEphelpers import get_contact_info
from pEphelpers import decryptusingsq
from pathlib import Path

@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_import_extra_key(settings, test_dirs, collect_email, extra_keypair, cmd_env):
    test_key_fpr = extra_keypair.fpr
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)

    # Run the command
    subprocess.run(['./pEpgate decrypt'], shell=True, capture_output=True,
                   input=collect_email, env=cmd_env)

    # Check that the key is in the pEp Database
    keys_db = test_dirs['work'] / test_email_to / '.pEp' / 'keys.db'
    db = sqlite3.connect(keys_db)
    keys = db.execute("SELECT primary_key FROM keys")
    assert test_key_fpr in [key[0] for key in keys]

@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_decrypt_message_no_key(collect_email, test_dirs, cmd_env):
    cmd_env['keys_dir'] = test_dirs['root'] / "_keys" # We point the command to a non-existing test dir
    res = subprocess.run(['./pEpgate decrypt'], shell=True,
            capture_output=True, input=collect_email, env=cmd_env)

    assert res.returncode == 7 # Return code 7 is "have_no_key"

@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_decrypt_message(settings, test_dirs, collect_email, extra_keypair, cmd_env):
    cmd_env['DEBUG'] = 'True'
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)
    subprocess.run(['./pEpgate decrypt'], shell=True,
            capture_output=True, input=collect_email, env=cmd_env)

    # We read the unencrypted email output for the data
    # TODO: Make sure this emails are only kept in debug mode
    decrypt_out_path = test_dirs['work'] / test_email_to / test_email_from
    out_folder = [f.path for f in os.scandir(decrypt_out_path)][0]
    decrypted = out_folder + '/in.decrypt.processed.eml'
    with open(decrypted) as decrypted_email:
        decrypted_data = decrypted_email.read()
    assert "Hello encrypted world!" in decrypted_data

@pytest.mark.xfail(reason="UnboundLocalError: local variable 'keyused' referenced before assignment") #FIXME
@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_sq_decrypt(collect_email, extra_keypair, test_dirs):
    key_path = test_dirs['keys'] / str(extra_keypair.fpr + '.sec.asc')
    dec_msg = decryptusingsq(collect_email, str(key_path))
    assert dec_msg is 0
