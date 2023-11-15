import os
import codecs
import logging
import sys

from datetime import datetime

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
            datetime.now().strftime("%Y.%m.%d-%H.%M.%S.%f"),
        )
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


def get_log_level(level_name):
    """
    Convert a log level name to its corresponding numeric value.

    Args:
        level_name (str): The log level name (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').

    Returns:
        int: The numeric value of the log level.

    Raises:
        ValueError: If the provided level_name is not a valid log level.
    """

    numeric_level = getattr(logging, level_name.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % level_name)

    return numeric_level


def init_logfile(level_name, console_logger, file_logger):
    """
    Initializes loggers with specified log level, handlers, and formatters for both console and file logging.

    Args:
        level_name (str): The log level name (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        console_logger (logging.Logger): Logger for console logging.
        file_logger (logging.Logger): Logger for file logging.

    Returns:
        None
    """

    numeric_level = get_log_level(level_name)
    console_logger.setLevel(level=numeric_level)
    file_logger.setLevel(level=numeric_level)

    # Create handlers
    log_folder = os.path.join(settings['home'], settings['work_dir'])
    os.makedirs(log_folder, exist_ok=True)
    log_file = os.path.join(log_folder, 'planckproxy.log')
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler(sys.stdout)

    # Set handler levels
    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)

    # Create formatter
    simple_formatter = logging.Formatter('%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
                                         datefmt='%d.%m.%Y %H:%M:%S')

    # Set formatter for handlers
    file_handler.setFormatter(simple_formatter)
    console_handler.setFormatter(simple_formatter)

    # Add handlers to loggers
    console_logger.addHandler(console_handler)
    file_logger.addHandler(file_handler)
