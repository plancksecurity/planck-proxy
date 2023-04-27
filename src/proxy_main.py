import os
import sys
import re
import codecs
import importlib
import traceback

from time import sleep
from glob import glob
from subprocess import Popen, PIPE

from proxy_settings import settings
from utils.printers import dbg, c, prettytable
from utils.parsers import get_contact_info, get_mail_headers
from utils.emails import dbgmail, sendmail, messageToSend, notifyHandshake
from utils.cryptography import decryptusingsq
from utils.hooks import cleanup


def init_lockfile():
    """
    Initialize lockfile.

    Args:
        None

    Returns:
        None
    """

    locktime = 0
    lockpid = None

    while os.path.isfile(settings["lockfilepath"]) and locktime < settings["locktimeout"]:
        lock = open(settings["lockfilepath"], "r")
        lockpid = lock.read()
        lock.close()
        if lockpid.isdigit() and int(lockpid) > 1:
            try:
                os.kill(int(lockpid), 0)
            except OSError:
                dbg(
                    "Lock held by dead PID " + lockpid + ", removing lockfile",
                    pub=False,
                )
                cleanup()
                lockpid = None
            else:
                dbg(
                    "Lock held by active PID "
                    + lockpid
                    + ", killing in "
                    + str(settings["locktimeout"] - locktime)
                    + "s",
                    pub=False,
                )
        else:
            dbg(
                "Lockfile doesn't contain any numeric PID [" + str(lockpid) + "]. Removing file",
                pub=False,
            )
            cleanup()
        locktime += 1
        sleep(1)

    if os.path.isfile(settings["lockfilepath"]) and lockpid is not None and lockpid.isdigit():
        lockpid = int(lockpid)
        if lockpid > 1:
            try:
                dbg("Sending SIGTERM to PID " + str(lockpid), pub=False)
                os.kill(lockpid, 15)
                sleep(1)
                dbg("Sending SIGKILL to PID " + str(lockpid), pub=False)
                os.kill(lockpid, 9)
                sleep(1)
            except Exception:
                pass

    lock = open(settings["lockfilepath"], "w")
    lock.write(str(os.getpid()))
    lock.close()
    dbg("Lockfile created", pub=False)


def get_message(message):
    """
    Reads a message from the standard input stream.

    Args:
        message (Message): The message object to store the read message.

    Returns:
        None.
    """

    dbg(
        "Reading message (to confirm press CTRL+D on an empty line)...",
        pub=False,
    )

    inbuf = bytearray()
    inmail = ""
    while True:
        part = sys.stdin.buffer.read(1024)
        if len(part) > 0:
            inbuf += part
        else:
            break

    try:
        for line in inbuf.decode(encoding="utf-8", errors="strict"):
            inmail += str(line)
    except Exception:
        try:
            dbg(c("Can't decode input message as utf-8, trying latin-1", 1))
            for line in inbuf.decode(encoding="latin-1", errors="strict"):
                inmail += str(line)
        except Exception:
            dbg(
                c(
                    "Can't decode input message as latin-1 either, doing utf-8 again but ignoring all errors",
                    1,
                )
            )
            for line in inbuf.decode(encoding="utf-8", errors="ignore"):
                inmail += str(line)

    if len(inmail) == 0:
        dbg(c("No message was passed to me. Aborting.", 1), pub=False)
        exit(2)

    message.msg["inmail"] = inmail


def set_addresses(message):
    """
    Determines the sender and recipient of the message, making "them" the sender of the message and
    "us" the recipient of the message.

    Args:
        message (Message): The message object to store the sender and recipient addresses, containing the
                            'msg', dictionary.

    Returns:
        None.
    """

    msgfrom, msgto = get_contact_info(message.msg["inmail"])

    message.msg["msgfrom"] = msgfrom
    message.msg["msgto"] = msgto

    # message.them["addr"] = msgfrom
    # message.us["addr"] = msgto


def enable_dts(message):
    """
    If sender enabled "Return receipt" and is part of the dts_domains setting, allow cleanup() to send back
    debugging info

    Args:
        message (Message): an instance of the Message class containing the parsed message in the 'msg' dictionary.

    Returns:
        None

    """
    global settings
    dts = get_mail_headers(message.msg["inmail"], "Disposition-Notification-To")  # Debug To Sender

    if len(dts) > 0:
        addr = dts[0]
        dts = "-".join(re.findall(re.compile(r"<?.*@(\w{2,}\.\w{2,})>?"), addr))
        dbg(c("Return receipt (debug log) requested by: " + str(addr), 3))
        if dts in settings["dts_domains"]:
            dbg(
                c(
                    "Domain " + c(dts, 5) + " is allowed to request a debug log",
                    2,
                )
            )
            settings["dts"] = addr
        else:
            dbg(c("Domain is not allowed to request a debug log", 1))


# ### Create & set working directory ################################################################


def init_workdir(message):
    """
    Create workdir for ouraddr, and set it to the current $HOME

    Args:
        message (Message): an instance of the Message class containing 'us' dictionary.

    Returns:
        None
    """

    global settings
    workdirpath = os.path.join(settings["home"], settings["work_dir"], message.msg["msgto"])
    if not os.path.exists(workdirpath):
        os.makedirs(workdirpath)

    os.environ["HOME"] = workdirpath
    os.chdir(workdirpath)

    settings["work_dir"] = workdirpath
    if settings["DEBUG"]:
        dbg(f"init workdir to {settings['work_dir']}")


# ## Check if Sequoia-DB already exists, if not import keys later using p≡p ########################


def check_initial_import():
    """
    Check if keys.db already exists, if not import keys later using p≡p
    """
    keys_db_path = os.path.join(os.environ["HOME"], ".pEp", "keys.db")
    return not os.path.exists(keys_db_path)


# ### Load p≡p ######################################################################################


def load_pep():
    """
    Import the p≡p engine. This will create the .pEp folder in the current $HOME This method should never be called
    before init_workdir, otherwise the .pEp folder would be located on the wrong folder.

    Returns:
        pEp (module): The p≡p engine module.
    """

    pEp = importlib.import_module("pEp")
    pEp.set_debug_log_enabled(True)  # TODO
    pEp.message_to_send = messageToSend
    pEp.notify_handshake = notifyHandshake

    dbg(
        "p≡p ("
        + str(pEp.about).strip().replace("\n", ", ")
        + ", p≡p engine version "
        + pEp.engine_version
        + ") loaded in",
        True,
    )
    return pEp


# ### Import static / globally available / extra keys ###############################################


def import_keys(pEp):
    """
    Imports keys from the keys_dir.

    Args:
        pEp (module): The p≡p engine module object.

    Returns:
        None.
    """
    dbg(c("Initializing keys.db...", 2))
    keys_path = os.path.join(settings["home"], settings["keys_dir"])
    key_files = glob(os.path.join(keys_path, "*.asc"))
    for f in key_files:
        keys = open(f, "rb").read()
        dbg("")
        pEp.import_key(keys)
        dbg("Imported key(s) from " + f, True)


# ### Prepare message for processing by planck #########################################################


def create_pEp_message(pEp, message):
    """
    Create a p≡p message object and store it in the message.msg['src'] key.

    Args:
        pEp (module): The p≡p engine module object.
        message (Message):  an instance of the Message class containing the 'msg' dictionary.

    Returns:
        None
    """
    try:
        src = pEp.Message(message.msg["inmail"])

        # Get rid of CC and BCC for loop-avoidance (since Postfix gives us one separate message per recipient)
        src.cc = []
        src.bcc = []

    except Exception:
        e = sys.exc_info()
        errmsg = "ERROR 4: " + str(e[0]) + ": " + str(e[1]) + "\n"
        errmsg += "Traceback:\n" + prettytable(
            [line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])]
        )
        dbg(errmsg)
        dbgmail(errmsg)
        exit(4)

    try:
        dbg(
            "Processing message from "
            + ((c(src.from_.username, 2)) if len(src.from_.username) > 0 else "")
            + c(" <" + src.from_.address + ">", 3)
            + " to "
            + ((c(src.to[0].username, 2)) if len(src.to[0].username) > 0 else "")
            + c(" <" + src.to[0].address + ">", 3)
        )
    except Exception:
        e = sys.exc_info()
        errmsg = "Couldn't get src.from_ or src.to\n"
        errmsg += "ERROR 5: " + str(e[0]) + ": " + str(e[1]) + "\n"
        errmsg += "Traceback:\n" + prettytable(
            [line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])]
        )
        dbg(errmsg)
        dbgmail(errmsg)
        exit(5)

    # Log parsed message

    logfilename = os.path.join(settings["logpath"], "in." + settings["mode"] + ".parsed.eml")
    dbg("p≡p-parsed message: " + c(logfilename, 6))
    logfile = codecs.open(logfilename, "w", "utf-8")
    logfile.write(str(src))
    logfile.close()

    message.msg["src"] = src


# ### Let p≡p do it's magic #########################################################################
def process_message(pEp, message):
    """
    Decrypt the message

    Args:
        pEp (module): The p≡p engine module object.
        message (Message):  an instance of the Message class containing the 'msg' dictionary.

    Returns:
        None
    """
    try:
        if settings["mode"] == "decrypt":
            # TODO: store some sort of failure-counter (per message ID?) to detect subsequent failures then
            #  fallback to sq, then forward as-is
            pepfails = False
            if not pepfails:
                dbg(c("Decrypting message via pEp...", 2))
                dst, keys, rating, flags = message.msg["src"].decrypt()
                dbg(c("Decrypted in", 2), True)
            else:
                dbg(c("Decrypting message via Sequoia...", 2))
                tmp = decryptusingsq(
                    message.msg["inmail"],
                    os.path.join(settings["keys_dir"], "sec.*.key"),
                )
                dst, keys, rating = (
                    pEp.Message(tmp[0]),
                    tmp[1],
                    None,
                )
                dbg(c("Decrypted in", 2), True)

            dbg(f"Message rating {rating}")

            if str(rating) == "have_no_key":
                keys_path = os.path.join(settings["home"], settings["keys_dir"])
                dbg(
                    c(
                        "No matching key found to decrypt the message. Please put a matching key into the "
                        + c(keys_path, 5)
                        + " folder. It will be sent encrypted to the scanner",
                        1,
                    )
                )
                # exit(7)
            else:
                if keys is None or len(keys) == 0:
                    dbg(c("Original message was NOT encrypted", 1))
                else:
                    dbg(c("Original message was encrypted to these keys", 2) + ":\n" + prettytable(list(set(keys))))

        # Workaround for engine converting plaintext-only messages into a msg.txt inline-attachment
        # dst = str(dst).replace(' filename="msg.txt"', "")

    except Exception:
        e = sys.exc_info()
        errmsg = "ERROR 7: " + str(e[0]) + ": " + str(e[1]) + "\n"
        errmsg += "Traceback:\n" + prettytable(
            [line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])]
        )
        dbg(errmsg)
        dbgmail(errmsg)
        exit(7)
        # Alternatively: fall back to forwarding the message as-is
        # dst, keys, rating, flags = src, None, None, None
        # pass

    message.msg["dst"] = dst

    # Log processed message
    logfilename = os.path.join(settings["logpath"], "in." + settings["mode"] + ".processed.eml")
    dbg("p≡p-processed message: " + c(logfilename, 6) + "\n" + str(dst)[0:1337])
    logfile = codecs.open(logfilename, "w", "utf-8")
    logfile.write(str(dst))
    logfile.close()


# ### Scan pipeline #################################################################################


def filter_message(message):
    """
    Run all the commands on the settings['scan_pipes'] for the message

    Args:
        message (Message):  an instance of the Message class containing the 'msg' dictionary.

    Returns:
        None
    """
    scanresults = {}
    desc = {0: "PASS", 1: "FAIL", 2: "RETRY"}
    cols = {0: 2, 1: 1, 2: 3}
    stdout = None
    stderr = None
    for filter in settings["scan_pipes"]:
        name = filter["name"]
        cmd = filter["cmd"]
        if settings["mode"] == "decrypt":
            dbg("Passing decrypted message to scanner " + c(name, 3))
            msgtoscan = str(message.msg["dst"])
        try:
            p = Popen(
                cmd.split(" "),
                shell=False,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
            )
            p.stdin.write(msgtoscan.encode("utf8"))
            stdout, stderr = p.communicate()
            rc = p.returncode
        except Exception:
            rc = 1
            dbg(f"Scanner {name} not available: {rc}")

        if rc in desc.keys():
            scanresults[name] = rc
            dbg("Result: " + c(desc[rc], cols[rc]))
        else:
            dbg("Unknown return code for scanner " + name + ": " + rc)

        if rc == 2:
            dbg(f"Error detected with scanner {name}")
            exit(11)

        if settings["DEBUG"]:
            if stdout and len(stdout) > 0:
                dbg(c("STDOUT:\n", 2) + prettytable(stdout.decode("utf8").strip().split("\n")))
            if stderr and len(stderr) > 0:
                dbg(c("STDERR:\n", 1) + prettytable(stderr.decode("utf8").strip().split("\n")))
            # dbg("Return code: " + c(str(rc), 3));

    dbg("Combined scan results:\n" + prettytable(scanresults))

    if sum(scanresults.values()) == 0:
        dbg("All scans " + c("PASSED", 2) + ", relaying message", 2)
    else:
        dbg("Some scans " + c("FAILED", 1) + ", not relaying message (keeping it in the Postfix queue for now)")
        admin_msg = f"A message from {message.msg['msgfrom']} and to {message.msg['msgfrom']} failed some of the scans."
        dbgmail(msg=admin_msg, subject="pEp Gate Scan failure")
        # sender_msg = f"Your message could not be delivered to {message.msg['msgto']}
        # because it failed some of our scans."
        # failurescanmail(sender_msg, message.msg['msgfrom'])
        exit(1)  # keep message on hold


def deliver_mail(message):
    """
    Send outgoing mail

    Args:
        message (Message):  an instance of the Message class containing the 'msg' dictionary.

    Returns:
        None

    """
    dbg("Sending mail")
    dbg(
        "From: "
        + ((c(message.msg["src"].from_.username, 2)) if len(message.msg["src"].from_.username) > 0 else "")
        + c(" <" + message.msg["src"].from_.address + ">", 3)
    )
    dbg(
        "  To: "
        + ((c(message.msg["src"].to[0].username, 2)) if len(message.msg["src"].to[0].username) > 0 else "")
        + c(" <" + message.msg["src"].to[0].address + ">", 3)
    )

    if settings["DEBUG"] and "discard" in message.msg["src"].to[0].address:
        dbg("Keyword discard found in recipient address, skipping call to sendmail")
    else:
        sendmail(message.msg["inmail"])

    dbg("===== " + c("p≡pGate ended", 1) + " =====")
