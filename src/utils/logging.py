import os
import codecs

from datetime import datetime

from .printers import dbg, c

from proxy_settings import settings


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
        message (Message):  an instance of the Message class containing the 'msg' and 'them' dictionaries.

    Returns:
        None
    """

    global settings
    logpath = os.path.join(
        settings["work_dir"],
        message.them["addr"],
        datetime.now().strftime("%Y.%m.%d-%H.%M.%S.%f"),
    )
    settings["logpath"] = logpath
    if not os.path.exists(logpath):
        os.makedirs(logpath)

    logfilename = os.path.join(logpath, "in." + settings["mode"] + ".original.eml")
    dbg("   Original message: " + c(logfilename, 6))  # + "\n" + inmail)
    logfile = codecs.open(logfilename, "w", "utf-8")
    logfile.write(message.msg["inmail"])
    logfile.close()

    if settings["DEBUG"]:
        dbg(f"init logpath to {settings['logpath']}")


def log_session():
    """
    Save per-session logfiles

    Args:
        None

    Returns:
        None
    """

    logfilename = os.path.join(settings["logpath"], "debug.log")
    logfile = codecs.open(logfilename, "w", "utf-8")
    logfile.write(getlog("textlog"))
    logfile.close()

    logfilename = os.path.join(settings["logpath"], "debug.html")
    logfile = codecs.open(logfilename, "w", "utf-8")
    logfile.write(getlog("htmllog"))
    logfile.close()
