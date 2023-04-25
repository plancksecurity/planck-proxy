import os
import re
import email
import sys
import traceback


from .printers import dbg, c

from proxy_settings import settings

# ## Parse args ##############################################################


def get_default(setting, type=str):
    """
    Get the default value for the given setting with the following priority:
    1. Env variable
    2. String on settings.py file (aka vars loaded into the memory space)

    Args:
        setting (str): The name of the setting to retrieve
        type (type, optional): The type to cast the value to. Defaults to str.

    Returns:
        Any: The value of the setting
    """
    env_val = os.getenv(setting)
    if env_val:
        if type is list:
            return env_val.split(" ")
        if type is bool:
            if env_val in ["True", "true", "1"]:
                return True
            return False
        return env_val
    return settings.get(setting)


def get_contact_info(inmail, reinjection=False):
    """
    Figure from and to address based on the email headers

    Args:
        inmail (str): The email message to extract information from
        reinjection (bool, optional): Flag to indicate whether to use Delivered-To header to find recipient.
            Defaults to False.

    Returns:
        Tuple[str, str]: A tuple containing the sender and recipient email addresses
    """

    mailparseregexes = [
        r"<([\w\-\_\"\.]+@[\w\-\_\"\.{1,}]+)>",
        r"<?([\w\-\_\"\.]+@[\w\-\_\"\.{1,}]+)>?",
    ]

    # Figure out the sender (use From header, fallback Return-Path)
    msgfrom = ""
    try:
        for mpr in mailparseregexes:
            msgfrom = "-".join(get_mail_headers(inmail, "From"))
            msgfrom = "-".join(re.findall(re.compile(mpr), msgfrom))
            if len(msgfrom) > 0:
                break
    except Exception:
        pass

    if msgfrom.count("@") != 1:
        dbg(c("Unparseable From-header, falling back to using Return-Path", 1))
        for mpr in mailparseregexes:
            msgfrom = "-".join(get_mail_headers(inmail, "Return-Path"))
            msgfrom = "-".join(re.findall(re.compile(mpr), msgfrom))
            if len(msgfrom) > 0:
                break
    # Figure out the recipient (rely on the Delivered-To header, rewrite if is a key in aliases map and if
    # any of it's values is part of To/CC/BCC)
    msgto = ""
    for hdr in ["To", "Delivered-To"] if reinjection else ["Delivered-To"]:
        try:
            for mpr in mailparseregexes:
                msgto = "-".join(get_mail_headers(inmail, hdr))
                msgto = "-".join(re.findall(re.compile(mpr), msgto))
                if len(msgto) > 0:
                    break
            if len(msgto) > 0:
                break  # we need one for each for-loop
        except Exception:
            pass

    if msgto.count("@") != 1:
        dbg(c("No clue how we've been contacted. Giving up...", 1))
        exit(3)

    msgfrom = msgfrom.lower()
    msgto = msgto.lower()

    return msgfrom, msgto


def get_mail_headers(inmsg, headername=None):
    """
    Extracts email headers from an email message.

    Args:
        inmsg (str): The email message as a string.
        headername (str or None): The name of the header to extract. If None, all headers are extracted.

    Returns:
        headers (list of str or dict): The extracted headers. If headername is None, a list of dictionaries with the
            header name as the key and the header value as the value is returned. If headername is not None,
            a list of strings with the header values is returned.
    """
    try:
        msg = email.message_from_string(inmsg)
        headers = []
        if headername is not None:
            h = msg.get_all(headername)
            if h is not None:
                headers = h
        else:
            origheaders = msg.items()
            for k, v in origheaders:
                vclean = []
                for line in v.splitlines():
                    vclean += [line.strip()]
                headers += [{k: "\n".join(vclean)}]
        return headers
    except Exception as e:
        dbg("Can't pre-parse e-mail. Aborting!")
        dbg("ERROR 21 - {}: {}".format(type(e).__name__, e))
        dbg("Traceback: " + str(traceback.format_tb(sys.exc_info()[2])))
        return False
