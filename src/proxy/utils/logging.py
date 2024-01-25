import os
import codecs

from datetime import datetime, timezone

from .printers import dbg, c
from .emails import dbgmail

from proxy.proxy_settings import settings
from proxy.utils.sanitizer import sanitize_email_address


def getlog(type):
    """
    Get the log content by type.

    Args:
        type (str): The type of the log content to retrieve.

    Returns:
        str: The log content.
    """
    return settings[type] if type in ["textlog", "htmllog"] else ""


def init_logging(message):
    """
    Log original message into the workdir

    Args:
        message (Message):  an instance of the Message class.

    Returns:
        None
    """


    try:
        global settings
        logpath = os.path.join(
            settings["work_dir"],
            sanitize_email_address(message.msgfrom),
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        )
        dbg("LOGPATH IS:" + logpath)
        settings["logpath"] = logpath
        if not os.path.exists(logpath):
            os.makedirs(logpath)

        logfilename = os.path.join(logpath, "in." + settings["mode"] + ".original.eml")
        dbg("   Original message: " + c(logfilename, 6))  # + "\n" + inmail)
        logfile = codecs.open(logfilename, "w", "utf-8")
        logfile.write(message.inmail)
        logfile.close()

        dbg(f"init logpath to {settings['logpath']}")

    except PermissionError:
        msg = (
            "Not enough permissions to create the logfile, please make sure that the process executing the proxy"
            + f'has permission to write in {settings["logpath"]}'
        )
        dbg(msg, log_level="ERROR")
        dbgmail(msg=msg, subject="planck Proxy permission failure")
        exit(8)


def log_session():
    """
    Save per-session logfiles

    Args:
        None

    Returns:
        None
    """
    try:
        logfilename = os.path.join(settings["logpath"], "planckproxy.log")
        logfile = codecs.open(logfilename, "w", "utf-8")
        logfile.write(getlog("textlog"))
        logfile.close()

        logfilename = os.path.join(settings["logpath"], "planckproxy.html")
        logfile = codecs.open(logfilename, "w", "utf-8")
        logfile.write(getlog("htmllog"))
        logfile.close()

    except PermissionError:
        msg = (
            "Not enough permissions to create the logfile, please make sure that the process executing the proxy"
            + f'has permission to write in {settings["logpath"]}'
        )
        dbg(msg, log_level="ERROR")
        dbgmail(msg=msg, subject="planck Proxy permission failure")
        exit(8)
