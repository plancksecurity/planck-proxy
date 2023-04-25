import os
import codecs
import sys
import html

from datetime import datetime
from collections import OrderedDict

from proxy_settings import settings


def print_init_info(args):
    """
    Print initialization information.

    Args:
        args (argparse.Namespace): Arguments.

    Returns:
        None
    """
    dbg(
        "===== "
        + c("p≡pGate started", 2)
        + " in mode "
        + c(settings["mode"], 3)
        + " | PID "
        + c(str(os.getpid()), 5)
        + " | UID "
        + c(str(os.getuid()), 6)
        + " | GID "
        + c(str(os.getgid()), 7)
        + " ====="
    )
    if settings["DEBUG"]:
        dbg(c("┌ Parameters", 5) + "\n" + prettytable(args.__dict__))
        cur_settings = settings.copy()
        for setting in ["adminlog", "textlog", "htmllog"]:
            cur_settings.pop(setting)
        dbg(c("┌ Settings (except logs)", 5) + "\n" + prettytable(cur_settings))


def print_summary_info(message):
    """
    Print summary information about the message and whether initial import is required

    Args:
        message (Message):  an instance of the Message class containing the 'msg' dictionary.

    Returns:
        None
    """

    from proxy_main import check_initial_import

    dbg("       Message from: " + c(str(message.msg["msgfrom"]), 5))
    dbg("         Message to: " + c(str(message.msg["msgto"]), 5))
    dbg("        Our address: " + c(message.us["addr"], 3))
    dbg("      Their address: " + c(message.them["addr"], 3))
    dbg("    Initital import: " + ("Yes" if check_initial_import() else "No"))


def print_keys_and_headers(message):
    """
    Print environment variables, keys in the keyring and headers in original message.

    Args:
        message (Message):  an instance of the Message class containing the 'msg' dictionary.

    Returns:
        None.
    """

    from .cryptography import keys_from_keyring
    from .parsers import get_mail_headers

    dbg(
        c("┌ Environment variables", 5) + "\n" + prettytable(os.environ),
        pub=False,
    )
    dbg(c("┌ Keys in this keyring (as stored in keys.db)", 5) + "\n" + prettytable(keys_from_keyring()))
    dbg(
        c("┌ Headers in original message (as seen by non-p≡p clients)", 5)
        + "\n"
        + prettytable(get_mail_headers(message.msg["inmail"]))
    )


# Debug and logging


def dbg(text, printtiming=False, pub=True):
    """
    Logs the given text with a timestamp and writes it to a log file.

    Args:
        text (str): The text to be logged.
        printtiming (bool, optional): If True, the time taken since the last log message is printed along
            with the message. Defaults to False.
        pub (bool, optional): If True, the message is added to the HTML logfile. Defaults to True.

    Returns:
        float: The time taken since the last log message was printed.
    """
    global settings
    thisactiontime = datetime.now()
    settings["thisactiontime"] = thisactiontime
    took = (thisactiontime - settings["lastactiontime"]).total_seconds()
    settings["lastactiontime"] = thisactiontime

    if len(text) == 0:  # don't output anything, only time the next event
        return took

    text = (
        c(thisactiontime.strftime("%d.%m.%Y %H:%M:%S.%f"), 3)
        + " "
        + str(text)
        + (" " + c("{:1.6f}".format(took) + "s", 5) if printtiming else "")
    )

    # Unconditionally write to the global logfile
    with codecs.open(settings["logfile"], "a+", "utf-8") as d:
        d.write(c(str(os.getpid()), 5) + " | " + text + "\n")
    d.close()

    if sys.stdout.isatty():
        print(text)

    settings["adminlog"] += toplain(text) + "\n"
    settings["textlog"] += text + "\n"

    if pub:
        settings["htmllog"] += tohtml(text) + "<br>\n"

    return took


def c(text, color=0):
    """
    Formats the text with the given color.

    Args:
        text (str): The text to be formatted.
        color (int): The color code to be applied to the text. Default is 0.

    Returns:
        str: The formatted text with the given color.
    """
    if text:
        return "\033[1;3" + str(color) + "m" + text + "\033[1;m"
    return ""


def toplain(text):
    """
    Converts the given text with ANSI escape codes to plain text.

    Args:
        text (str): A string containing ANSI escape codes.

    Returns:
        A plain text string with the ANSI escape codes removed.
    """
    ret = text
    ret = ret.replace("\033[1;30m", "")
    ret = ret.replace("\033[1;31m", "")
    ret = ret.replace("\033[1;32m", "")
    ret = ret.replace("\033[1;33m", "")
    ret = ret.replace("\033[1;34m", "")
    ret = ret.replace("\033[1;35m", "")
    ret = ret.replace("\033[1;36m", "")
    ret = ret.replace("\033[1;37m", "")
    ret = ret.replace("\033[1;m", "")
    return ret


def tohtml(text):
    """
    Convert text to HTML format with color-coded text.

    Args:
        text (str): The input text to be converted.

    Returns:
        str: The converted HTML text.
    """

    ret = text
    ret = html.escape(ret, True)
    ret = ret.replace("\n", "<br>\n")
    ret = ret.replace(" ", "&nbsp;")
    ret = ret.replace("\033[1;30m", '<font color="#000000">')  # black
    ret = ret.replace("\033[1;31m", '<font color="#ff0000">')  # red
    ret = ret.replace("\033[1;32m", '<font color="#00bb00">')  # green
    ret = ret.replace("\033[1;33m", '<font color="#ff8800">')  # yellow
    ret = ret.replace("\033[1;34m", '<font color="#0000ff">')  # blue
    ret = ret.replace("\033[1;35m", '<font color="#ff00ff">')  # pink
    ret = ret.replace("\033[1;36m", '<font color="#5555ff">')  # bright-blue
    ret = ret.replace("\033[1;37m", '<font color="#666666">')  # white
    ret = ret.replace("\033[1;m", "</font>")
    return ret


def prettytable(thing, colwidth=26):
    """
    Returns a pretty-printed table of the given data.

    Args:
        thing (Union[str, bool, Dict, List[Dict]]): The data to display in the table.
        colwidth (int, optional): The width of each column. Default is 26.

    Returns:
        str: The pretty-printed table.
    """
    ret = ""
    if not isinstance(thing, list):
        thing = [thing]

    for subthing in thing:
        if isinstance(subthing, str):
            ret += (" " * colwidth) + c(" | ", 5) + subthing + "\n"
        elif isinstance(subthing, bool):
            ret += (" " * colwidth) + c(" | ", 5) + str(subthing) + "\n"
        elif hasattr(subthing, "__iter__"):
            for k, v in subthing.items():
                w = []
                keys = []

                if isinstance(v, dict) or isinstance(v, OrderedDict):
                    maxkeylength = max(len(x) for x in v.keys())
                    w += [prettytable(v, max(maxkeylength, 10))]
                    v = "\n".join(w)

                if isinstance(v, list):
                    # Iterate over list to figure out if we have dicts underneath + it's max key length
                    maxkeylength = colwidth
                    for item in v:
                        if isinstance(item, dict) or isinstance(item, OrderedDict):
                            keys += item.keys()

                    if len(keys) > 0:
                        maxkeylength = max(len(x) for x in keys)

                    if len(v) == 0:
                        w = ["None"]

                    # Iterate another round with the known max key length, call prettytable() recursively for
                    # "sub-tables"
                    for item in v:
                        if isinstance(item, dict) or isinstance(item, OrderedDict):
                            w += [prettytable(item, max(maxkeylength, 10))]
                        else:
                            w += [item]
                    v = "\n".join(w)

                ret += (
                    c(str(k).rjust(colwidth), 6)
                    + c(" | ", 5)
                    + str(v).replace("\n", "\n" + (" " * colwidth) + c(" | ", 5))
                    + "\n"
                )

        else:
            dbg("Don't know how to prettyprint this thing. Aborting!")
            sys.exit(20)

    return ret[:-1]
