from pEphelpers import sendmail

msg = """From: <root@backup.pep.security>
Delivered-To: dbe@pep.security
To: "David" <dbe@pep.security>
Subject: Hello world!
Date: Thu, 12 Jul 2021 09:59:45 +0200

Hello encrypted world!"""


def test_send():
    res = sendmail(msg)
    assert res is True

