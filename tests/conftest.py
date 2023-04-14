import os
import glob
import random
import string
import pytest
import shutil

import pEphelpers
import pEpgatemain

from dataclasses import dataclass
from pathlib import Path
from pEpgatesettings import init_settings
from pEpgate import Message
from unittest.mock import Mock


@dataclass
class Key:
    name: str
    address: str
    fpr: str


EXTRA_KEY = Key("extra", "proxy@test.com", "3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3")
BOB_KEY = Key("bob", "bob@pep.security", "CC47DB45FDAF07712F1D9F5BFE0D6DE1B8C05AE8")
ALICE_KEY = Key("alice", "alice@pep.security", "6002754A3B0551D9729E28168AD5EEE0A979C126")


@dataclass
class MockpEpMessage:
    opt_fields: dict = None

    def __str__(self):
        return f"{self.opt_fields}"


@dataclass
class MockpEpId:
    address: str = ""


@pytest.fixture
def pEp():
    pEp = Mock()
    pEp.engine_version = "1.0.0"
    return pEp


@pytest.fixture
def test_dirs(tmp_path):
    return {
        "tmp": tmp_path,
        "root": Path(os.environ["TEST_ROOT"]),
        "project_root": Path(os.environ["PROJECT_ROOT"]),
        "keys": tmp_path / "keys",
        "test_keys": Path(os.environ["TEST_ROOT"]) / "test_keys",
        "work": tmp_path / "work",
        "emails": Path(os.environ["TEST_ROOT"]) / "emails",
    }


@pytest.fixture
def extra_keypair(test_dirs):
    pubkey = test_dirs["test_keys"] / str(EXTRA_KEY.fpr + ".pub.asc")
    privkey = test_dirs["test_keys"] / str(EXTRA_KEY.fpr + ".sec.asc")

    if not os.path.exists(test_dirs["keys"]):
        os.makedirs(test_dirs["keys"])

    shutil.copy(pubkey, test_dirs["keys"])
    shutil.copy(privkey, test_dirs["keys"])
    return EXTRA_KEY


@pytest.fixture
def bob_key(test_dirs):
    pubkey = test_dirs["test_keys"] / str(BOB_KEY.fpr + ".pub.asc")

    if not os.path.exists(test_dirs["keys"]):
        os.makedirs(test_dirs["keys"])

    shutil.copy(pubkey, test_dirs["keys"])
    return BOB_KEY


@pytest.fixture
def alice_key(test_dirs):
    pubkey = test_dirs["test_keys"] / str(ALICE_KEY.fpr + ".pub.asc")

    if not os.path.exists(test_dirs["keys"]):
        os.makedirs(test_dirs["keys"])

    shutil.copy(pubkey, test_dirs["keys"])
    return ALICE_KEY


@pytest.fixture
def message():
    return Message()


@pytest.fixture
def obtain_key_db(test_dirs):
    db_location = os.path.join(test_dirs["root"], "test_db")
    src_folder = os.path.join(db_location, ".pEp")
    dest_folder = str(test_dirs["tmp"])

    if os.path.exists(dest_folder):
        shutil.rmtree(dest_folder)

    shutil.copytree(src_folder, dest_folder)

    return dest_folder


@pytest.fixture
def mailbot_address():
    """
    Get a random address for a pEp mailbot
    """
    return (
        "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=16))
        + "@test.pep.security"
    )


@pytest.fixture
def collect_email(request):
    """
    Get the contents of a file in the /tests/emails/ folder where the filename matches the expr
    """
    email = glob.glob(os.environ["TEST_ROOT"] + "/emails/" + request.param)[0]
    with open(email, "rb") as f:
        return f.read()


@pytest.fixture
def settings_file(test_dirs):
    """
    Get the settings file path for tests.

    This is intended to be used with the  --settings_file parameter in the integration tests
    """
    settings_file = test_dirs["root"] / "tests_settings" / "settings_tests.json"
    return settings_file


@pytest.fixture
def set_settings(settings_file):
    """
    Init the settings with the settings file for tests.

    This is intended to set the correct globals befor running any pEpGate code.
    """

    return init_settings(settings_file)


@pytest.fixture
def test_settings_dict(test_dirs, extra_keypair):
    """
    Set the basic test_settings that will be used to overwrite the defaults on 'settings_tests.json'
    """
    test_settings = {
        "work_dir": str(test_dirs["work"]),
        "keys_dir": str(test_dirs["keys"]),
        "test-nomails": True,
        "EXTRA_KEYS": [extra_keypair.fpr],
        "DEBUG": True,
    }
    return test_settings


@pytest.fixture(autouse=True)
def run_before_and_after_tests(monkeypatch, tmp_path, set_settings):
    """Fixture to execute asserts before and after a test is run"""
    os.environ["HOME"] = str(tmp_path)

    # overwrite sendmail for tests
    monkeypatch.setattr(pEpgatemain, "sendmail", lambda msg: True)
    monkeypatch.setattr(pEphelpers, "sendmail", lambda msg: True)

    yield  # this is where the testing happens

    pEphelpers.cleanup()
