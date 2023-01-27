from pEphelpers import sendmail
import pytest
import sys


@pytest.mark.parametrize('collect_email', ["test_send_bot.eml"], indirect=True)
def test_send(collect_email, mailbot_address):
    test_msg = collect_email.replace('[[TO_ADDR]]', mailbot_address)
    if sys.platform == 'darwin':
    # No server in a darwin system, so sendmail will fail
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            res = sendmail(test_msg)
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 6
    else:
        res = sendmail(test_msg)

