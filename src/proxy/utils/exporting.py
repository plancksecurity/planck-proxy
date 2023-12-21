import os
import codecs

from datetime import datetime, timezone

from .printers import dbg, c
from .emails import dbgmail

from proxy.proxy_settings import settings
from proxy.utils.logging import getlog


def init_exporting(message):
    """
    Log original message into the workdir

    Args:
        message (Message):  an instance of the Message class.

    Returns:
        None
    """

    try:
        global settings
        exportpath = os.path.join(
            settings["export_dir"],
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S.%fZ")
        )
        settings["exportpath"] = exportpath
        dbg("Export path is: " + exportpath)
        if not os.path.exists(exportpath):
            os.makedirs(exportpath)

        dbg(f"init exportpath to {settings['exportpath']}")

    except PermissionError:
        msg = (
            "Not enough permissions to create the logfile, please make sure that the process executing the proxy"
            + f'has permission to write in {settings["exportpath"]}'
        )
        dbg(msg)
        dbgmail(msg=msg, subject="planck Proxy permission failure")
        exit(8)


def export_session():
    """
    Save per-session logfiles

    Args:
        None

    Returns:
        None
    """
    try:

        exportfilename = os.path.join(settings["exportpath"], "planckproxy.log")
        exportfile = codecs.open(exportfilename, "w", "utf-8")
        exportfile.write(getlog("textlog"))
        exportfile.close()

    except PermissionError:
        msg = (
            "Not enough permissions to create the logfile, please make sure that the process executing the proxy"
            + f'has permission to write in {settings["logpath"]}'
        )
        dbg(msg)
        dbgmail(msg=msg, subject="planck Proxy permission failure")
        exit(8)
