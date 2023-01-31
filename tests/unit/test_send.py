from pEphelpers import sendmail
import pytest
import sys


@pytest.mark.skipif(sys.platform  == 'darwin', reason="No server in a darwin system, so sendmail will fail")
@pytest.mark.parametrize('collect_email', ["test_send_bot.eml"], indirect=True)
def test_send(collect_email, mailbot_address):
    test_msg = collect_email.replace('[[TO_ADDR]]', mailbot_address)
    res = sendmail(test_msg)
