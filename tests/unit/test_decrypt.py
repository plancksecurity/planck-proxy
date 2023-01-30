import subprocess
import shutil
import sqlite3
import os
import pytest
from pEphelpers import get_contact_info

@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_import_extra_key(collect_email):
    work_dir = 'tests/work'
    keys_dir = 'tests/keys'
    test_key_fpr = '3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3'
    test_email_from, test_email_to = get_contact_info(collect_email)
    cmd_env = os.environ.copy()
    cmd_env['work_dir'] = work_dir
    cmd_env['keys_dir'] = keys_dir

    # Make sure work dir is clean and that we have our test key
    shutil.rmtree(work_dir, ignore_errors=True)
    assert os.path.isdir(work_dir) is False
    assert os.path.isdir(keys_dir) is True

    # Run the command
    with open('tests/emails/basic.enc.eml', 'rb') as email:
        subprocess.run(['./pEpgate decrypt'], shell=True,
            capture_output=True, input=email.read(), env=cmd_env)

    # Check that the key is in the pEp Database
    keys_db = work_dir + '/' + test_email_to + '/.pEp/keys.db'
    db = sqlite3.connect(keys_db)
    keys = db.execute("SELECT primary_key FROM keys")
    assert test_key_fpr in [key[0] for key in keys]
    shutil.rmtree(work_dir, ignore_errors=True)


def test_decrypt_message_no_key():
    cmd_env = os.environ.copy()
    work_dir = 'tests/work'
    keys_dir = 'tests/_keys' # We point the command to a non-existing test dir
    cmd_env['work_dir'] = work_dir
    cmd_env['keys_dir'] = keys_dir
    with open('tests/emails/basic.enc.eml', 'rb') as email:
        res = subprocess.run(['./pEpgate decrypt'], shell=True,
            capture_output=True, input=email.read(), env=cmd_env)

    assert res.returncode is 7 # Return code 7 is "have_no_key"
    shutil.rmtree(work_dir, ignore_errors=True)


@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_decrypt_message(collect_email):
    cmd_env = os.environ.copy()
    work_dir = 'tests/work'
    keys_dir = 'tests/keys'
    cmd_env['work_dir'] = work_dir
    cmd_env['keys_dir'] = keys_dir
    cmd_env['DEBUG'] = 'True'
    test_email_from, test_email_to = get_contact_info(collect_email)
    with open('tests/emails/basic.enc.eml', 'rb') as email:
        subprocess.run(['./pEpgate decrypt'], shell=True,
            capture_output=True, input=email.read(), env=cmd_env)

    # We read the unencrypted email output for the data
    # TODO: Make sure this emails are only kept in debug mode
    decrypt_out_path = work_dir + '/' + test_email_to + '/' + test_email_from
    out_folder = [f.path for f in os.scandir(decrypt_out_path)][0]
    decrypted = out_folder + '/in.decrypt.processed.eml'
    with open(decrypted) as decrypted_email:
        decrypted_data = decrypted_email.read()
    assert "Hello back, I am encrypted!" in decrypted_data
    shutil.rmtree(work_dir, ignore_errors=True)


