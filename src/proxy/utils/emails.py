import re
import smtplib
import socket
import os
import base64

from .printers import dbg, c
from .parsers import get_contact_info

from proxy.proxy_settings import settings


def sendmail(msg):
    """
    Send an email message using the settings STMP_HOST and STMP_PORT

    Args:
        msg (str): The message to be sent.

    Returns:
        None
    """
    if settings.get("test-nomails"):
        dbg("Test mode, mail sending skip")
        return
    # Replace dots at the beginning of a line with the MIME-encoded,
    # quoted-printable counterpart. Fuck you very much, Outlook!
    msg = re.sub("^\.", "=2E", msg, flags=re.M)  # noqa

    # We must NEVER pass a Delivered-To header back into the MTA
    # The next hop might think it's part of a mail loop when it sees it's own hostname "again"
    msg = re.sub("^Delivered-To:.*\n", "", msg, flags=re.M)

    dbg(f"Sending message:\n{msg}")
    try:
        msgfrom, msgto = get_contact_info(msg, True)
        with smtplib.SMTP(settings["SMTP_HOST"], settings["SMTP_PORT"]) as server:
            server.sendmail(msgfrom, msgto, msg.encode("utf8"))
    except Exception as e:
        dbg(c(f"ERROR 6 - Mail could not be sent, return code: {e}", 6))
        exit(6)
    else:
        dbg("Mail successfully sent")


def failurescanmail(msg, rcpt, subject="planck Proxy Scan failure"):
    """
    Sends a notification email in case of a scanning failure.

    Args:
        msg (str): The message body of the email.
        rcpt (str): The email address of the recipient.
        subject (str): The subject of the email. Default is "planck Proxy Scan failure".

    Returns:
        None
    """
    dbg("Sending scanning notification failure to to " + c(rcpt, 2))
    mailcontent = "Content-type: text/plain; charset=UTF-8\n"
    mailcontent += "From: proxy@" + socket.getfqdn() + "\n"
    mailcontent += "To: " + rcpt + "\n"
    mailcontent += "Subject: " + subject + "\n\n"
    mailcontent += msg + "\n"
    sendmail(mailcontent)


def dbgmail(
    msg,
    rcpt=None,
    subject="[FATAL] planck proxy @ " + socket.getfqdn() + " crashed!",
    attachments=[],
):
    """
    Sends a debug mail with given parameters.

    Args:
        msg (str): The body of the mail
        rcpt (str): The recipient of the mail. If None, uses the email address in the settings.
        subject (str): The subject of the mail. Defaults to '[FATAL] pEp Gate @ ' + socket.getfqdn() + ' crashed!'
        attachments (list): A list of strings, paths to files that should be attached to the mail

    Returns:
        None
    """
    if rcpt is None:
        # cant use a global in method default arg
        rcpt = settings["admin_addr"]

    # We're in failure-mode here so we can't rely on pEp here and need to hand-craft a MIME-structure
    dbg("Sending message to " + c(rcpt, 2) + ", subject: " + c(subject, 3))

    if len(attachments) == 0:
        mailcontent = "Content-type: text/html; charset=UTF-8\n"
    else:
        mailcontent = 'Content-Type: multipart/mixed; boundary="pEpMIME"\n'

    mailcontent += "From: proxy@" + socket.getfqdn() + "\n"
    mailcontent += "To: " + rcpt + "\n"
    mailcontent += "Subject: " + subject + "\n\n"

    if len(attachments) > 0:
        mailcontent += "This is a multi-part message in MIME format.\n"
        mailcontent += "--pEpMIME\n"
        mailcontent += "Content-Type: text/html; charset=UTF-8\n"
        mailcontent += "Content-Transfer-Encoding: 7bit\n\n"

    mailcontent += "<html><head><style>"
    mailcontent += ".console { font-family: Courier New; font-size: 13px; line-height: 14px; width: 100%; }"
    mailcontent += "</style></head>"
    mailcontent += '<body topmargin="0" leftmargin="0" marginwidth="0" marginheight="0"><table class="console"><tr><td>'
    mailcontent += (
        msg + "<br>" + ("=" * 80) + "<br><br>" if len(msg) > 0 else ""
    ) + settings["htmllog"]
    mailcontent += "</td></tr></table></body></html>"

    if len(attachments) > 0:
        for att in attachments:
            dbg("Attaching " + att)

            mailcontent += "\n\n--pEpMIME\n"
            mailcontent += (
                'Content-Type: application/octet-stream; name="'
                + os.path.basename(att)
                + '"\n'
            )
            mailcontent += (
                'Content-Disposition: attachment; filename="'
                + os.path.basename(att)
                + '"\n'
            )
            mailcontent += "Content-Transfer-Encoding: base64\n\n"

            with open(att, "rb") as f:
                mailcontent += base64.b64encode(f.read()).decode()

        mailcontent += "--pEpMIME--"

    sendmail(mailcontent)


# Sync & echo protocol handling (unused for now) ########################


def messageToSend(msg):
    pass
    # dbg("Ignoring message_to_send", pub=False)
    # dbg(c("messageToSend(" + str(len(str(msg))) + " Bytes)", 3))
    # dbg(str(msg))


def notifyHandshake(me, partner, signal):
    pass
    # dbg("Ignoring notify_handshake", pub=False)
    # dbg("notifyHandshake(" + str(me) + ", " + str(partner) + ", " + str(signal) + ")")
