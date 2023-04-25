from src.utils.emails import sendmail
import pytest
import sys


@pytest.mark.skipif(
    sys.platform == "darwin",
    reason="No server in a darwin system, so sendmail will fail",
)
@pytest.mark.parametrize("collect_email", ["test_send_bot.eml"], indirect=True)
def test_send(collect_email, mailbot_address):
    email = collect_email.decode()
    test_msg = email.replace("[[TO_ADDR]]", mailbot_address)
    sendmail(test_msg)
