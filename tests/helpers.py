import os
import glob
import random
import string


def get_mailbot_address():
    """
    Get a random address for a pEp mailbot
    """
    return ''.join(
        random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=16)
        ) + '@test.pep.security'


def collect_email(expr):
    """
    Get the contents of a file in the /tests/emails/ folder where the filename matches the expr
    """
    email = glob.glob(os.environ["TEST_ROOT"] + '/emails/' + expr)[0]
    with open(email) as f:
        return f.read()
