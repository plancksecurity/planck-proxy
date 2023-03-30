import subprocess
import sqlite3
import os
import shutil
import pytest
from src.scripts.deletekeyfromkeyring import delete_key
from pEphelpers import get_contact_info, dbg
from override_settings import override_settings
from pathlib import Path


def test_delete_key(set_settings, settings_file, test_dirs, bob_key, alice_key, obtain_key_db):
    test_key_fpr = bob_key.fpr
    test_email_from = bob_key.address
    test_email_to = alice_key.address

    delete_key(test_email_to, test_email_from, str(test_dirs['tmp']))

    # Check that the key is in the pEp Database
    keys_db = os.path.join(str(obtain_key_db), 'keys.db')
    db = sqlite3.connect(keys_db)
    keys = db.execute("SELECT primary_key FROM keys")
    assert test_key_fpr not in [key[0] for key in keys]
