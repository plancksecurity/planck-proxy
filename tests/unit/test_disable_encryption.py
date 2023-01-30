import subprocess
import shutil
import os
import pytest
from pEphelpers import get_contact_info


@pytest.mark.parametrize('collect_email', ["basic_noencrypt.eml"], indirect=True)
def test_encrypt_message(collect_email):
    cmd_env = os.environ.copy()
    work_dir = 'tests/work'
    keys_dir = 'tests/keys'
    cmd_env['work_dir'] = work_dir
    cmd_env['keys_dir'] = keys_dir
    test_email_from, test_email_to = get_contact_info(collect_email)
    with open('tests/emails/basic_noencrypt.eml', 'rb') as email:
        subprocess.run(['./pEpgate encrypt --DEBUG'], shell=True,
            capture_output=True, input=email.read(), env=cmd_env)

    decrypt_out_path = work_dir + '/' + test_email_from + '/' + test_email_to
    out_folder = [f.path for f in os.scandir(decrypt_out_path)][0]
    encrypted = out_folder + '/in.encrypt.processed.eml'
    with open(encrypted) as encrypted_email:
        encrypted_data = encrypted_email.read()
    assert "Hello proxy" in encrypted_data
    assert "NOENCRYPT" not in encrypted_data
    shutil.rmtree(work_dir, ignore_errors=True)

@pytest.mark.xfail(reason="bob's key needs to be in the keys dir")
@pytest.mark.parametrize('collect_email', ["basic_noencrypt.eml"], indirect=True)
def test_encrypt_message_no_debug(collect_email):
    cmd_env = os.environ.copy()
    work_dir = 'tests/work'
    keys_dir = 'tests/keys'
    cmd_env['work_dir'] = work_dir
    cmd_env['keys_dir'] = keys_dir
    test_email_from, test_email_to = get_contact_info(collect_email)
    with open('tests/emails/basic_noencrypt.eml', 'rb') as email:
        subprocess.run(['./pEpgate encrypt'], shell=True,
            capture_output=True, input=email.read(), env=cmd_env)

    decrypt_out_path = work_dir + '/' + test_email_from + '/' + test_email_to
    out_folder = [f.path for f in os.scandir(decrypt_out_path)][0]
    encrypted = out_folder + '/in.encrypt.processed.eml'
    with open(encrypted) as encrypted_email:
        encrypted_data = encrypted_email.read()
    assert "Hello proxy" not in encrypted_data
    # shutil.rmtree(work_dir, ignore_errors=True)
