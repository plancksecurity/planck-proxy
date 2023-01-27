import os
import glob
import random
import string
import pathlib
import pytest

@pytest.hookimpl(trylast=True)  # run after configure for TempPathFactory
def pytest_configure(config):
    """
    Change HOME to point to the base directory for this test session.
    """
    # FIXME: Find a official way to get this here
    global TEST_HOME
    TEST_HOME = config._tmp_path_factory.getbasetemp()
    # TODO: Fix: Does not work for Windows
    os.environ["HOME"] = str(TEST_HOME)

def per_user_directory():
    # BUG: This assumes Engine internals
    # TODO: Fix: Does not work for Windows
    return pathlib.Path(os.environ["HOME"]) / ".pEp"


@pytest.fixture
def reset_pep_folder(tmp_path):
    # TODO: Fix: Does not work for Windows
    os.environ["HOME"] = str(tmp_path)
    os.environ["PEP_HOME"] = str(tmp_path)
    pep_folder = per_user_directory()
    assert not pep_folder.exists()
    pep_folder.mkdir(parents=True)
    return pep_folder


KEYS_DIR = pathlib.Path(__file__).parent.absolute() / "testing_keys"

@pytest.fixture
def keys_dir():
    return KEYS_DIR

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
    with open(email) as f:
        return f.read()
