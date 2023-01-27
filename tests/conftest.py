import os
import glob
import random
import string
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
