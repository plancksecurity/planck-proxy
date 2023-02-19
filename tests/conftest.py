import os
import glob
import random
import string
import pytest
import shutil
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
ALICE_KEY = Key('alice', 'alice@pep.security', "")

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
    return Path(os.environ["HOME"]) / ".pEp"

@pytest.fixture
def test_dirs(tmp_path):
    return {
        'tmp': tmp_path,
        'root': Path(os.environ['TEST_ROOT']),
        'keys': tmp_path / "keys",
        'test_keys': Path(os.environ['TEST_ROOT']) / "test_keys",
        'work': tmp_path / "work",
        'emails': Path(os.environ['TEST_ROOT']) / "emails",
    }

@pytest.fixture
def reset_pep_folder(tmp_path):
    # TODO: Fix: Does not work for Windows
    os.environ["HOME"] = str(tmp_path)
    os.environ["PEP_HOME"] = str(tmp_path)
    pep_folder = per_user_directory()
    assert not pep_folder.exists()
    pep_folder.mkdir(parents=True)
    return pep_folder

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
    with open(email) as f:
        return f.read()

@pytest.fixture
def settings():
    return init_settings()

@pytest.fixture
def get_dummy_dir(test_dirs):
    dummy_route = (f"{test_dirs['root']}/dummy_filter.py")
    return dummy_route