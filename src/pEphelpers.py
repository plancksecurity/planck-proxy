import codecs
import os
import html
import sys
import re
import smtplib
import socket
import base64
import sqlite3
import shutil
import io
import tempfile
import email
import traceback
import json


from collections import OrderedDict
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT
from glob import glob

from pEpgatesettings import settings

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
    dbg(c("!!! pEp Gate - Unhandled exception !!!", 1))
    mailcontent = ""
    for line in traceback.format_exception(type, value, tback):
        dbg(line.strip())
        mailcontent += line
    dbgmail(mailcontent)
    exit(31)


def cleanup():
    """
    Cleans up the system by removing the lockfile if it exists and removing
    log files if debug mode is not activated. If dts is not None, sends a
    debug email with the log files as attachments.

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
            "[DEBUG LOG] pEp Gate @ " + socket.getfqdn(),
            attachments,
        )

    lockfilepath = settings["lockfilepath"]
    if os.path.isfile(lockfilepath):
        try:
            os.remove(lockfilepath)
            dbg("Lockfile " + c(lockfilepath, 6) + " removed", pub=False)
        except Exception:
            dbg("Can't remove Lockfile " + c(lockfilepath, 6), pub=False)

    logpath = settings["logpath"]
    if settings["DEBUG"]:
        dbg(
            f"Debug mode, will keep the logged output messages in the work_dir {c(logpath, 6)}",
            pub=False,
        )
    else:
        try:
            shutil.rmtree(logpath)
            dbg("Log folder " + c(logpath, 6) + " removed", pub=False)
        except Exception as e:
            dbg("Can't remove log folder " + c(logpath, 6) + str(e), pub=False)
        try:
            main_log = os.path.join(settings["home"], "debug.log")
            os.remove(main_log)
            # We use a print so we don't create a new log :)
            print("Main log " + c(main_log, 6) + " removed")
        except Exception as e:
            dbg("Can't remove main log " + c(main_log, 6) + str(e), pub=False)


# Debug and logging


def dbg(text, printtiming=False, pub=True):
    """
    Logs the given text with a timestamp and writes it to a log file.

    Args:
        text (str): The text to be logged.
        printtiming (bool, optional): If True, the time taken since the last
            log message is printed along with the message. Defaults to False.
        pub (bool, optional): If True, the message is added to the HTML log
            file. Defaults to True.

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

    # text = c(str(os.getpid()).rjust(5, " "), 5) + " | " +
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


def getlog(type):
    """
    Get the log content by type.

    Args:
        type (str): The type of the log content to retrieve.

    Returns:
        str: The log content.
    """
    return settings[type] if type in ["textlog", "htmllog"] else ""


def sendmail(msg):
    """
    Send an email message.

    Args:
        msg (str): The message to be sent.

    Raises:
        ValueError: If the message argument is not a string.

    Returns:
        None
    """
    if settings.get("test-nomails"):
        dbg("Test mode, mail sending skip")
        return
    # Replace dots at the beginning of a line with the MIME-encoded,
    # quoted-printable counterpart. Fuck you very much, Outlook!
    msg = re.sub("^\.", "=2E", msg, flags=re.M)
    try:
        msgfrom, msgto = get_contact_info(msg, True)
        with smtplib.SMTP(settings["SMTP_HOST"], settings["SMTP_PORT"]) as server:
            server.sendmail(msgfrom, msgto, msg.encode("utf8"))
    except Exception as e:
        dbg(c(f"ERROR 6 - Mail could not be sent, return code: {e}", 6))
        exit(6)
    else:
        dbg("Mail successfully sent")


def failurescanmail(msg, rcpt, subject="pEp Gate Scan failure"):
    """
    Sends a notification email in case of a scanning failure.

    Args:
        msg (str): The message body of the email.
        rcpt (str): The email address of the recipient.
        subject (str): The subject of the email. Default is "pEp Gate Scan failure".

    Returns:
        None
    """
    dbg("Sending scanning notification failure to to " + c(rcpt, 2))
    mailcontent = "Content-type: text/plain; charset=UTF-8\n"
    mailcontent += "From: pepgate@" + socket.getfqdn() + "\n"
    mailcontent += "To: " + rcpt + "\n"
    mailcontent += "Subject: " + subject + "\n\n"
    mailcontent += msg + "\n"
    sendmail(mailcontent)


def dbgmail(
    msg,
    rcpt=None,
    subject="[FATAL] pEp Gate @ " + socket.getfqdn() + " crashed!",
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

    mailcontent += "From: pepgate@" + socket.getfqdn() + "\n"
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


# Set variables in the outer scope from within the inner scope "pEpgatemain"


def setoutervar(var, val):
    """
    Set a variable in the global scope.

    Args:
        var (str): The name of the variable to set.
        val (Any): The value to assign to the variable.

    Returns:
        None
    """
    globals()[var] = val


# ## pEp Sync & echo protocol handling (unused for now) ########################


def messageToSend(msg):
    pass
    # dbg("Ignoring message_to_send", pub=False)
    # dbg(c("messageToSend(" + str(len(str(msg))) + " Bytes)", 3))
    # dbg(str(msg))


def notifyHandshake(me, partner, signal):
    pass
    # dbg("Ignoring notify_handshake", pub=False)
    # dbg("notifyHandshake(" + str(me) + ", " + str(partner) + ", " + str(signal) + ")")


def prettytable(thing, colwidth=26):
    """
    Returns a pretty-printed table of the given data.

    Args:
        thing (Union[str, bool, Dict, List[Dict]]): The data to display in the table.

    Optional Args:
        colwidth (int): The width of each column. Default is 26.

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


def keysfromkeyring(userid=None):
    """
    Args:
        userid (str): (Optional) The user ID to look up key for. Default is None.

    Returns:
        List of dictionaries representing all the keys in the keyring if there are any, otherwise False.
        Each dictionary contains two key-value pairs:
        - 'pEp_keys.db': a dictionary with three keys ('UserID', 'KeyID', 'Subkeys'), each containing a string value.
        - 'key_blob': a dictionary with two keys ('is_private', 'sq_inspect'), 'is_private' being a boolean value and
          'sq_inspect' being a list of strings.
    """
    sq_bin = settings["sq_bin"]
    db = sqlite3.connect(os.path.join(os.environ["HOME"], ".pEp", "keys.db"))

    if userid is not None:
        dbg("Looking up key of " + c(userid, 5) + " from keyring...")

    def collate_email(a, b):
        return 1 if a > b else -1 if a < b else 0

    db.create_collation("EMAIL", collate_email)

    allkeys = []

    if userid is not None:
        q1 = db.execute("SELECT * FROM userids WHERE userid = ?;", (userid,))
    else:
        q1 = db.execute("SELECT * FROM userids;")

    for r1 in q1:
        q2 = db.execute("SELECT * FROM subkeys WHERE primary_key = ?;", (r1[1],))
        subkeys = []
        for r2 in q2:
            subkeys += [str(r2[0])]

        fromdb = {}
        fromdb["UserID"] = r1[0]
        fromdb["KeyID"] = r1[1]
        fromdb["Subkeys"] = subkeys

        q3 = db.execute("SELECT tpk, secret FROM keys WHERE primary_key = ?;", (r1[1],))
        for r3 in q3:
            sqkeyfile = (
                ("sec" if r3[1] is True else "pub") + "." + r1[0] + "." + r1[1] + ".key"
            )
            open(sqkeyfile, "wb").write(r3[0])
            cmd = [sq_bin, "enarmor", sqkeyfile, "-o", sqkeyfile + ".asc"]
            p = Popen(
                cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE
            )  # stderr=STDOUT for debugging
            ret = p.wait()

            cmd = [sq_bin, "inspect", "--certifications", sqkeyfile]
            p = Popen(
                cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE
            )  # stderr=STDOUT for debugging
            ret = p.wait()

            if ret == 0:
                inspected = {}
                inspected["is_private"] = r3[1]
                inspected["sq_inspect"] = []
                for line in io.TextIOWrapper(
                    p.stdout, encoding="utf-8", errors="strict"
                ):
                    line = line.strip()
                    inspected["sq_inspect"] += [line]

                # Hide internal filename & extra whitespace
                inspected["sq_inspect"] = inspected["sq_inspect"][2:]

                usernameparseregexes = [
                    r"UserID: (.*?) <?[\w\-\_\"\.]+@[\w\-\_\"\.{1,}]+>?\n?",
                    r"UserID: (.*?) <[\w\-\_\"\.]+@[\w\-\_\"\.{1,}]+>\n?",
                    r"UserID: ([\w\-\_\"\.\ ]+)\n?",
                ]
                for upr in usernameparseregexes:
                    try:
                        patt = re.compile(upr, re.MULTILINE | re.DOTALL)
                        inspected["username"] = patt.findall(
                            "\n".join(inspected["sq_inspect"])
                        )[0]
                        if len(inspected["username"]) > 0:
                            break
                    except Exception:
                        pass

                if len(inspected["username"]) == 0:
                    dbg(
                        "[!] No username/user ID was contained in this PGP blob. Full sq inspect:\n"
                        + "\n".join(inspected["sq_inspect"])
                    )

        allkeys += [{"pEp_keys.db": fromdb, "key_blob": inspected}]

    db.close()

    if len(allkeys) > 0:
        return allkeys
    else:
        return False


def inspectusingsq(PGP):
    """
    Inspects the given PGP blob using Sequoia.

    Args:
        PGP (str): The PGP blob to be inspected.

    Returns:
        None
    """
    sq_bin = settings["sq_bin"]
    tf = tempfile.NamedTemporaryFile()
    tf.write(PGP.encode("utf8"))
    cmd = [sq_bin, "inspect", "--certifications", tf.name]
    p = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    p.wait()

    for line in io.TextIOWrapper(p.stdout, encoding="utf-8", errors="strict"):
        line = line.strip()
        dbg(line)


def decryptusingsq(inmail, secretkeyglob):
    """
    Decrypts a PGP message using the sq CLI tool.

    Args:
        inmail (str): The PGP message to decrypt.
        secretkeyglob (str): A file glob pattern matching the secret key(s) to use for decryption.

    Returns:
        List[Union[str, List[str]]]: A list containing two elements:
            - A string representing the decrypted message(s) without the 'X-pEp-Wrapped-Message-Info: INNER' tag.
            - A list containing the key ID(s) used for decryption.
    """
    sq_bin = settings["sq_bin"]
    ret = ""
    patt = re.compile(
        r"-----BEGIN PGP MESSAGE-----.*?-----END PGP MESSAGE-----",
        re.MULTILINE | re.DOTALL,
    )
    pgpparts = patt.findall(inmail)

    dbg(c("[!] Fallback-decrypting via sq CLI tool", 1))
    # dbg("Inmail: " + str(inmail))
    # dbg("PGP: " + str(pgpparts))

    if len(pgpparts) == 0:
        return c("No -----BEGIN PGP MESSAGE----- found in original message", 3)

    for p in pgpparts:
        tmppath = "/tmp/pEpgate.pgppart." + str(os.getpid())
        if "=0A=" in p:
            import quopri

            p = quopri.decodestring(p).decode("utf-8")

        # dbg("PGP part: " + c(p, 5))
        open(tmppath, "w").write(str(p))

        for secretkey in glob(secretkeyglob):
            dbg(c("Trying secret key file " + secretkey, 3))
            cmd = [sq_bin, "decrypt", "--recipient-key", secretkey, "--", tmppath]
            # dbg("CMD: " + " ".join(cmd), pub=False)
            p = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            rc = p.returncode
            # dbg("STDOUT: " + c(stdout.decode("utf8"), 2))
            # dbg("STDERR: " + c(stderr.decode("utf8"), 1))
            # dbg("Return code: " + c(str(rc), 3));
            if rc == 0:
                keyused = [re.search(r"[0-9a-zA-Z]{40}", secretkey)[0]]
                break

        os.unlink(tmppath)

        if len(stdout) > 0:
            patt = re.compile(r"Message-ID:.*?^$", re.MULTILINE | re.DOTALL)
            pepparts = patt.findall(stdout.decode("utf8"))
            ret += "\n".join(pepparts)

    return [ret.replace("X-pEp-Wrapped-Message-Info: INNER\r\n", ""), keyused]


def getmailheaders(inmsg, headername=None):
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
            msgfrom = "-".join(getmailheaders(inmail, "From"))
            msgfrom = "-".join(re.findall(re.compile(mpr), msgfrom))
            if len(msgfrom) > 0:
                break
    except Exception:
        pass

    if msgfrom.count("@") != 1:
        dbg(c("Unparseable From-header, falling back to using Return-Path", 1))
        for mpr in mailparseregexes:
            msgfrom = "-".join(getmailheaders(inmail, "Return-Path"))
            msgfrom = "-".join(re.findall(re.compile(mpr), msgfrom))
            if len(msgfrom) > 0:
                break
    # Figure out the recipient (rely on the Delivered-To header, rewrite if is a key in aliases map and if
    # any of it's values is part of To/CC/BCC)
    msgto = ""
    for hdr in ["To", "Delivered-To"] if reinjection else ["Delivered-To"]:
        try:
            for mpr in mailparseregexes:
                msgto = "-".join(getmailheaders(inmail, hdr))
                msgto = "-".join(re.findall(re.compile(mpr), msgto))
                if len(msgto) > 0:
                    break
            if len(msgto) > 0:
                break  # we need one for each for-loop
        except Exception:
            pass

    aliases_map_path = os.path.join(settings["home"], settings["aliases_map"])
    aliases = jsonlookup(aliases_map_path, msgto, False)
    if aliases is not None:
        dbg("Delivered-To is an aliased address: " + c(", ".join(aliases), 3))

        allrcpts = set()
        for hdr in ("To", "CC", "BCC"):
            try:
                for a in ", ".join(getmailheaders(inmail, hdr)).split(", "):
                    for mpr in mailparseregexes:
                        rcpt = " ".join(re.findall(re.compile(mpr), a))
                        if len(rcpt) > 0:
                            allrcpts.add(rcpt)
            except Exception:
                # dbg("No " + hdr + " header in this message")
                pass

        dbg("All recipients / Alias candidates: " + c(", ".join(allrcpts), 5))
        for r in allrcpts:
            if r in aliases:
                dbg("Matching alias found: " + c(r, 2))
                msgto = r
                break
        else:
            dbg(c("Couldn't match alias to original Delivered-To!", 1))

    if msgto.count("@") != 1:
        dbg(c("No clue how we've been contacted. Giving up...", 1))
        exit(3)

    msgfrom = msgfrom.lower()
    msgto = msgto.lower()

    return msgfrom, msgto


def jsonlookup(jsonmapfile, key, bidilookup=False):
    dbg("JSON lookup in file " + jsonmapfile + " for key " + key)
    result = None

    with open(jsonmapfile) as f:
        j = json.load(f)
    try:
        result = j[key]
        dbg(c("Forward-rewriting ", 2) + key + " to " + str(result))
    except KeyError:
        pass

    if result is None and bidilookup:
        try:
            for k, v in j.items():
                if type(v) is list:
                    if key in v:
                        result = k
                        break
                else:
                    jr = {v: k for k, v in j.items()}
                    result = jr[key]
                    break
            dbg(c("Reverse-rewriting ", 3) + key + " to " + str(result))
        except KeyError:
            pass

    # Optional: redirect backscatter messages to an admin
    """
    if jsonmapfile == fwdmappath and result is None:
        dbg("Username part: " + key[:key.rfind("@")])
        if key[:key.rfind("@")] in ("root", "postmaster", "noreply", "no-reply"):
            result = j['default']
    dbg(c("Fallback-rewriting ", 2) + key + " to " + result)
    """

    return result
