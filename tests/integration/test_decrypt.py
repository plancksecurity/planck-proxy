import subprocess
import sqlite3
import os
import pytest
from src.utils.parsers import get_contact_info
from compare_mails import get_email_body
from override_settings import override_settings


@pytest.mark.parametrize("collect_email", ["basic.enc.eml"], indirect=True)
def test_import_extra_key(
    settings_file,
    test_dirs,
    collect_email,
    extra_keypair,
    test_settings_dict,
):
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)
    settings_file = override_settings(test_dirs, settings_file, test_settings_dict)

    # Run the command
    command = f"./planckProxy decrypt --settings_file {settings_file}"
    p = subprocess.run([command], shell=True, capture_output=True, input=collect_email)
    assert p.stderr == b""
    assert p.returncode == 0

    # Check that the key is in the pEp Database
    keys_db = test_dirs["work"] / test_email_to / ".pEp" / "keys.db"
    db = sqlite3.connect(keys_db)
    keys = db.execute("SELECT primary_key FROM keys")
    assert extra_keypair.fpr in [key[0] for key in keys]


@pytest.mark.parametrize("collect_email", ["basic.noextra.enc.eml"], indirect=True)
def test_decrypt_message_no_key(
    set_settings,
    settings_file,
    collect_email,
    test_dirs,
    extra_keypair,
    test_settings_dict,
):
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)

    settings_file = override_settings(test_dirs, settings_file, test_settings_dict)

    # Run the command
    command = f"./planckProxy decrypt --settings_file {settings_file}"
    p = subprocess.run([command], shell=True, capture_output=True, input=collect_email)

    assert p.stderr == b""
    assert p.returncode == 0

    decrypt_out_path = test_dirs["work"] / test_email_to / test_email_from
    out_folder = [f.path for f in os.scandir(decrypt_out_path)][0]
    decrypted = out_folder + "/in.decrypt.processed.eml"
    with open(decrypted) as decrypted_email:
        decrypted_data = decrypted_email.read()

    # Check that the processed email is the same as the input one (still encrypted)
    assert get_email_body(collect_email.decode()) == get_email_body(decrypted_data)


@pytest.mark.parametrize("collect_email", ["basic.enc.eml"], indirect=True)
def test_decrypt_message(
    set_settings,
    settings_file,
    test_dirs,
    collect_email,
    extra_keypair,
    test_settings_dict,
):
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)
    settings_file = override_settings(test_dirs, settings_file, test_settings_dict)

    command = f"./planckProxy decrypt --settings_file {settings_file}"
    p = subprocess.run([command], shell=True, capture_output=True, input=collect_email)

    assert p.stderr == b""
    assert p.returncode == 0

    decrypt_out_path = test_dirs["work"] / test_email_to / test_email_from
    out_folder = [f.path for f in os.scandir(decrypt_out_path)][0]
    decrypted = out_folder + "/in.decrypt.processed.eml"
    with open(decrypted) as decrypted_email:
        decrypted_data = decrypted_email.read()
    assert "Hello encrypted world!" in decrypted_data
