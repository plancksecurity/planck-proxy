import subprocess
import sqlite3
import pytest
from override_settings import override_settings
from src.utils.parsers import get_contact_info


@pytest.mark.parametrize("collect_email", ["basic.enc.eml"], indirect=True)
def test_import_extra_key(
    set_settings,
    settings_file,
    test_dirs,
    collect_email,
    extra_keypair,
    test_settings_dict,
):
    test_key_fpr = extra_keypair.fpr
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
    assert test_key_fpr in [key[0] for key in keys]
