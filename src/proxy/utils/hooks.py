import os
import socket
import shutil
import traceback

from glob import glob

from .printers import dbg, c
from .emails import dbgmail

from proxy.proxy_settings import settings
from proxy.planckProxy import console_logger, file_logger


# ## Exception / post-execution handling #####################################


def except_hook(type, value, tback):
    """
    Custom exception hook to handle unhandled exceptions and log them via email

    Args:
        type (type): The type of the exception.
        value (Exception): The exception instance.
        tback (traceback): The traceback object associated with the exception.

    Returns:
        None
    """
    dbg(c("!!! planck proxy - Unhandled exception !!!", 1), log_level="ERROR")
    mailcontent = ""
    for line in traceback.format_exception(type, value, tback):
        dbg(line.strip(), log_level="ERROR")
        mailcontent += line
    dbgmail(mailcontent)
    exit(31)


def cleanup():
    """
    Cleans up the system by removing the lockfile if it exists and removing log files if debug mode is not activated.
    If dts is not None, sends a debug email with the log files as attachments.

    Args:
        None

    Returns:
        None
    """
    if settings["dts"] is not None:
        attachments = []
        logpath = settings["logpath"]
        if logpath is not None:
            for a in glob(os.path.join(logpath, "*.eml")):
                attachments += [a]
        dbgmail(
            "As requested via activated Return Receipt here's your debug log:",
            settings["dts"],
            "[DEBUG LOG] planck Proxy @ " + socket.getfqdn(),
            attachments,
        )

    lockfilepath = settings["lockfilepath"]
    if os.path.isfile(lockfilepath):
        try:
            os.remove(lockfilepath)
            dbg("Lockfile " + c(lockfilepath, 6) + " removed", pub=False)
        except Exception:
            dbg("Can't remove Lockfile " + c(lockfilepath, 6), pub=False, log_level="ERROR")

    logpath = settings["logpath"]
    if console_logger.getEffectiveLevel() <= 10: #DEBUG
        dbg(
            f"Debug mode, will keep the logged output messages and emails in the work_dir {c(logpath, 6)}",
            pub=False,
        )
    else:
        try:
            shutil.rmtree(logpath)
            dbg("Log folder " + c(logpath, 6) + " removed", pub=False)
        except Exception as e:
            dbg("Can't remove log folder " + c(logpath, 6) + str(e), pub=False, log_level="ERROR")
