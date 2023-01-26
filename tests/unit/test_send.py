from pEphelpers import sendmail
from helpers import get_mailbot_address
from helpers import collect_email


def test_send():
    to_addr = get_mailbot_address()
    test_msg = collect_email("test_send_bot.eml").replace('[[TO_ADDR]]', to_addr)
    res = sendmail(test_msg)
    assert res is True

