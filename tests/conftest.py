import os
import glob
import pytest
import shutil

from dataclasses import dataclass
from pathlib import Path

from proxy.proxy_settings import settings, init_settings
from proxy.utils.hooks import cleanup


@dataclass
class Key:
    name: str
    address: str
    fpr: str


EXTRA_KEY = Key("extra", "proxy@test.com", "3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3")


@pytest.fixture
def test_dirs(tmp_path):
    """
    Create a dictionary with the paths needed for tests and some temporary folders
    """
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
    """
    Copy the extra key in the keys directory in the temporary folder
    """
    pubkey = test_dirs["test_keys"] / str(EXTRA_KEY.fpr + ".pub.asc")
    privkey = test_dirs["test_keys"] / str(EXTRA_KEY.fpr + ".sec.asc")

    if not os.path.exists(test_dirs["keys"]):
        os.makedirs(test_dirs["keys"])

    shutil.copy(pubkey, test_dirs["keys"])
    shutil.copy(privkey, test_dirs["keys"])
    return EXTRA_KEY


@pytest.fixture
def obtain_key_db(test_dirs):
    """
    Copy the test .pEp database into a temporary folder and return a path to it
    """
    db_location = os.path.join(test_dirs["root"], "test_db")
    src_folder = os.path.join(db_location, ".pEp")
    dest_folder = str(test_dirs["tmp"])

    if os.path.exists(dest_folder):
        shutil.rmtree(dest_folder)

    shutil.copytree(src_folder, dest_folder)

    return dest_folder


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

    This is intended to set the correct globals before running any planckProxy code.
    """

    return init_settings(settings_file)


@pytest.fixture
def test_settings_dict(test_dirs):
    """
    Set the basic test_settings that will be used to overwrite the defaults on 'settings_tests.json'
    """
    test_settings = {
        "work_dir": str(test_dirs["work"]),
        "keys_dir": str(test_dirs["keys"]),
        "test-nomails": True,
        "DEBUG": True,
    }
    return test_settings


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmp_path, set_settings):
    """Fixture to execute asserts before and after a test is run"""
    os.environ["HOME"] = str(tmp_path)
    os.chdir(str(tmp_path))

    yield  # this is where the testing happens

    cleanup()
