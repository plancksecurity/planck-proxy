import os
import glob
import random
import string
import pytest
import shutil
import json

import pEphelpers
import pEpgatemain

from dataclasses import dataclass
from pathlib import Path
from pEpgatesettings import settings, init_settings

@dataclass
class Key:
    name: str
    address: str
    fpr: str



EXTRA_KEY = Key('extra', 'proxy@test.com', "3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3")
BOB_KEY = Key('bob', 'bob@pep.security', "CC47DB45FDAF07712F1D9F5BFE0D6DE1B8C05AE8")
ALICE_KEY = Key('alice', 'alice@pep.security', "6002754A3B0551D9729E28168AD5EEE0A979C126")


@pytest.fixture
def test_dirs(tmp_path):
    return {
        'tmp': tmp_path,
        'root': Path(os.environ['TEST_ROOT']),
        'project_root': Path(os.environ['PROJECT_ROOT']),
        'keys': tmp_path / "keys",
        'test_keys': Path(os.environ['TEST_ROOT']) / "test_keys",
        'work': tmp_path / "work",
        'emails': Path(os.environ['TEST_ROOT']) / "emails",
    }

# @pytest.fixture
# def reset_pep_folder(tmp_path):
#     # TODO: Fix: Does not work for Windows
#     os.environ["HOME"] = str(tmp_path)
#     os.environ["PEP_HOME"] = str(tmp_path)
#     pep_folder = per_user_directory()
#     assert not pep_folder.exists()
#     pep_folder.mkdir(parents=True)
#     return pep_folder

@pytest.fixture
def extra_keypair(test_dirs):
    pubkey = test_dirs['test_keys'] / str(EXTRA_KEY.fpr + '.pub.asc')
    privkey = test_dirs['test_keys'] / str(EXTRA_KEY.fpr + '.sec.asc')

    if not os.path.exists(test_dirs['keys']):
        os.makedirs(test_dirs['keys'])

    shutil.copy(pubkey, test_dirs['keys'])
    shutil.copy(privkey, test_dirs['keys'])
    return EXTRA_KEY

@pytest.fixture
def bob_key(test_dirs):
    pubkey = test_dirs['test_keys'] / str(BOB_KEY.fpr + '.pub.asc')

    if not os.path.exists(test_dirs['keys']):
        os.makedirs(test_dirs['keys'])

    shutil.copy(pubkey, test_dirs['keys'])
    return BOB_KEY

@pytest.fixture
def mailbot_address():
    """
    Get a random address for a pEp mailbot
    """
    return ''.join(
        random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=16)
        ) + '@test.pep.security'

@pytest.fixture
def collect_email(request):
    """
    Get the contents of a file in the /tests/emails/ folder where the filename matches the expr
    """
    email = glob.glob(os.environ["TEST_ROOT"] + '/emails/' + request.param)[0]
    with open(email, 'rb') as f:
        return f.read()

@pytest.fixture
def settings_file(test_dirs):
    
    settings_file = os.path.join(test_dirs['tmp'], 'settings_tests.json')

    test_settings = {
        "scan_pipes": [
        {"name": "SpamAssassin", "cmd": "ls"},
        {"name": "ClamAV", "cmd": "ls"}
        ]
    }

    json_object = json.dumps(test_settings, indent=4)

    with open(settings_file, "w") as outfile:
        outfile.write(json_object)

    return settings_file

@pytest.fixture
def set_settings():
    settings = init_settings()


@pytest.fixture
def cmd_env(test_dirs):
    """
    Set the basic environment values to run a subprocess command
    """
    cmd_env = os.environ.copy()
    cmd_env['work_dir'] = test_dirs['work']
    cmd_env['keys_dir'] = test_dirs['keys']
    return cmd_env

@pytest.fixture(autouse=True)
def run_before_and_after_tests(monkeypatch, set_settings, tmp_path):
    """Fixture to execute asserts before and after a test is run"""
    os.environ['HOME'] = str(tmp_path)

    # overwrite sendmail for tests
    monkeypatch.setattr(pEpgatemain, "sendmail", lambda msg: True)
    monkeypatch.setattr(pEphelpers, "sendmail", lambda msg: True)

    yield # this is where the testing happens

    pEphelpers.cleanup()

