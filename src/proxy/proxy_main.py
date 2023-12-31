import os
import sys
import re
import codecs
import importlib
import traceback
import shutil

from time import sleep
from glob import glob
from subprocess import Popen, PIPE

from proxy.proxy_settings import settings
from proxy.utils.printers import dbg, c, prettytable
from proxy.utils.parsers import get_contact_info, get_mail_headers
from proxy.utils.emails import dbgmail, sendmail, messageToSend, notifyHandshake
from proxy.utils.cryptography import decryptusingsq
from proxy.utils.hooks import cleanup
from proxy.utils.sanitizer import sanitize_email_address


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

    if settings["file"]:
        with open(settings["file"], "rb") as file:
            data = file.read()
        inbuf = data
        dbg("Data has been read")

    else:
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
            dbg(c("Can't decode input message as utf-8, trying latin-1", 1), log_level="WARNING")
            for line in inbuf.decode(encoding="latin-1", errors="strict"):
                inmail += str(line)
        except Exception:
            dbg(
                c(
                    "Can't decode input message as latin-1 either, doing utf-8 again but ignoring all errors",
                    1,
                ), log_level="WARNING"
            )
            for line in inbuf.decode(encoding="utf-8", errors="ignore"):
                inmail += str(line)

    if len(inmail) == 0:
        dbg(c("No message was passed to me. Aborting.", 1), pub=False, log_level="ERROR")
        exit(2)

    # message.msg["inmail"] = inmail
    message.inmail = inmail


def set_addresses(message):
    """
    Determines the sender and recipient of the message, and stores the "from" and "to" addresses in the message object

    Args:
        message (Message): The message object to store the sender and recipient addresses.

    Returns:
        None.
    """

    msgfrom, msgto = get_contact_info(message.inmail)

    message.msgfrom = msgfrom
    message.msgto = msgto


def enable_dts(message):
    """
    If sender enabled "Return receipt" and is part of the dts_domains setting, allow cleanup() to send back
    debugging info

    Args:
        message (Message): an instance of the Message class.

    Returns:
        settings (dict): the settings dictionary

    """
    global settings
    dts = get_mail_headers(message.inmail, "Disposition-Notification-To")  # Debug To Sender

    if len(dts) > 0:
        addr = dts[0]
        dts = "-".join(re.findall(re.compile(r"<?.*@(\w{2,}\.\w{2,})>?"), addr))
        dbg(c("Return receipt (debug log) requested by: " + str(addr), 3))
        if dts in settings["dts_domains"]:
            dbg(c("Domain " + c(dts, 5) + " is allowed to request a debug log", 2))
            settings["dts"] = addr
        else:
            dbg(c("Domain is not allowed to request a debug log", 1), log_level="WARNING")


# ### Create & set working directory ################################################################


def init_workdir(message):
    """
    Create workdir for the message recipient, and set it to the current $HOME. Then check if HOME folder exists and create otherwise

    Args:
        message (Message): an instance of the Message class.

    Returns:
        None
    """

    global settings
    workdirpath = os.path.join(settings["home"], settings["work_dir"], sanitize_email_address(message.msgto))
    if not os.path.exists(workdirpath):
        os.makedirs(workdirpath)

    os.environ["HOME"] = workdirpath
    os.chdir(workdirpath)

    settings["work_dir"] = workdirpath
    dbg(f"init workdir to {settings['work_dir']}")

    if os.name != "posix":
        # On windows, set the local app data folder to be the same as the workdir so the databases can be created correctly
        os.environ["LOCALAPPDATA"] = settings["work_dir"]

    if not os.path.exists(settings["home"]):
        os.makedirs(settings["home"])


# ## Create & set export directory

def init_exportdir(message):
    """
    Create export for the message sender, and set it to the current $HOME.

    Args:
        message (Message): an instance of the Message class.

    Returns:
        None
    """

    global settings
    exportdirpath = os.path.join(settings["home"], settings["export_dir"], sanitize_email_address(message.msgfrom))
    if not os.path.exists(exportdirpath):
        os.makedirs(exportdirpath)


    settings["export_dir"] = exportdirpath
    dbg(f"init exportdir to {settings['export_dir']}")


# ## Check if Sequoia-DB already exists, if not import keys later using planck ########################


def check_initial_import():
    """
    Check if keys.db already exists, if not import keys later using planck
    """

    keys_db_path = os.path.join(os.environ["HOME"], settings["database_folder"], "keys.db")
    return not os.path.exists(keys_db_path)


# ### Load planck ######################################################################################


def load_planck():
    """
    Import the planck core. This will create the .pEp folder in the current $HOME This method should never be called
    before init_workdir, otherwise the .pEp folder would be located on the wrong folder.

    Returns:
        planck (module): The planck core module.
    """

    planck = importlib.import_module("pEp")
    planck.set_debug_log_enabled(True)  # TODO
    planck.message_to_send = messageToSend
    planck.notify_handshake = notifyHandshake

    if os.name != "posix":
        # On windows we need to manually trigger the database creation
        try:
            planck.import_key("")
        except ValueError:
            pass

    databases = ["management.db", "keys.db"]
    for database in databases:
        db_path = os.path.join(settings["work_dir"], settings["database_folder"], database)
        if not os.path.exists(db_path):
            blank_db_path = os.path.join(settings["project_root"], "data", database)
            shutil.copy(blank_db_path, db_path)
            dbg(f"{database} not found, using empty backup.")

    dbg(
        "planck core ("
        + str(planck.about).strip().replace("\n", ", ")
        + ", planck core version "
        + planck.engine_version
        + ") loaded in",
        True,
    )
    return planck


# ### Import static / globally available / extra keys ###############################################


def import_keys(planck):
    """
    Imports keys from the keys_dir.

    Args:
        planck (module): The planck core module object.

    Returns:
        None.
    """
    dbg(c("Initializing keys.db...", 2))
    keys_path = os.path.join(settings["home"], settings["keys_dir"])
    key_files = glob(os.path.join(keys_path, "*.asc"))
    for f in key_files:
        keys = open(f, "rb").read()
        dbg("")
        planck.import_key(keys)
        dbg("Imported key(s) from " + f, True)


# ### Prepare message for processing by planck #########################################################


def create_planck_message(planck, message):
    """
    Create a planck message object and store it in the message.inmail_parsed.

    Args:
        planck (module): The planck core module object.
        message (Message):  an instance of the Message class.

    Returns:
        None
    """
    try:
        inmail_parsed = planck.Message(message.inmail)

        # Get rid of CC and BCC for loop-avoidance (since Postfix gives us one separate message per recipient)
        inmail_parsed.cc = []
        inmail_parsed.bcc = []

    except Exception:
        e = sys.exc_info()
        errmsg = "ERROR 4: " + str(e[0]) + ": " + str(e[1]) + "\n"
        errmsg += "Traceback:\n" + prettytable(
            [line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])]
        )
        dbg(errmsg, log_level="ERROR")
        dbgmail(errmsg)
        exit(4)

    try:
        from_username = inmail_parsed.from_.username
        from_address = inmail_parsed.from_.address

        from_username_part = c(from_username, 2) if from_username and len(from_username) > 0 else ""
        from_address_part = c(" <" + from_address + ">", 3)

        to_address_part = c(" <" + message.msgto + ">", 3)

        dbg(f"Processing message from {from_username_part}{from_address_part} to {to_address_part}", log_level="INFO")

    except Exception:
        e = sys.exc_info()
        errmsg = "Couldn't get inmail_parsed.from_ or inmail_parsed.to\n"
        errmsg += "ERROR 5: " + str(e[0]) + ": " + str(e[1]) + "\n"
        errmsg += "Traceback:\n" + prettytable(
            [line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])]
        )
        dbg(errmsg, log_level="ERROR")
        dbgmail(errmsg)
        exit(5)

    # Log parsed message

    logfilename = os.path.join(settings["logpath"], "in." + settings["mode"] + ".parsed.eml")
    dbg("planck-parsed message: " + c(logfilename, 6))
    logfile = codecs.open(logfilename, "w", "utf-8")
    logfile.write(str(inmail_parsed))
    logfile.close()

    message.inmail_parsed = inmail_parsed


# ### Let the planck core do it's magic #########################################################################
def process_message(planck, message):
    """
    Decrypt the message and store in the message.inmail_decrypted attribute.

    Args:
        planck (module): The planck core module object.
        message (Message):  an instance of the Message class.

    Returns:
        None
    """
    try:
        if settings["mode"] == "decrypt":
            # TODO: store some sort of failure-counter (per message ID?) to detect subsequent failures then
            #  fallback to sq, then forward as-is
            planckfails = False
            if not planckfails:
                dbg(c("Decrypting message via planck...", 2), log_level="INFO")
                inmail_decrypted, keys, rating, flags = message.inmail_parsed.decrypt()
                dbg(c("Decrypted in", 2), True)
            else:
                dbg(c("Decrypting message via Sequoia...", 2))
                tmp = decryptusingsq(
                    message.inmail,
                    os.path.join(settings["keys_dir"], "sec.*.key"),
                )
                inmail_decrypted, keys, rating = (
                    planck.Message(tmp[0]),
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
                    ), log_level="WARNING"
                )
                # exit(7)
            else:
                if keys is None or len(keys) == 0:
                    dbg(c("Original message was NOT encrypted", 1), log_level="INFO")
                else:
                    dbg(c("Original message was encrypted to these keys", 2) + ":\n" + prettytable(list(set(keys))), log_level="INFO")

        # Workaround for engine converting plaintext-only messages into a msg.txt inline-attachment
        # dst = str(dst).replace(' filename="msg.txt"', "")

    except Exception:
        e = sys.exc_info()
        errmsg = "ERROR 7: " + str(e[0]) + ": " + str(e[1]) + "\n"
        errmsg += "Traceback:\n" + prettytable(
            [line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])]
        )
        dbg(errmsg, log_level="ERROR")
        dbgmail(errmsg)
        exit(7)
        # Alternatively: fall back to forwarding the message as-is
        # dst, keys, rating, flags = src, None, None, None
        # pass

    message.inmail_decrypted = inmail_decrypted

    # Log processed message
    logfilename = os.path.join(settings["logpath"], "in." + settings["mode"] + ".processed.eml")
    dbg("Log planck-processed message: " + c(logfilename, 6) + "\n" + str(inmail_decrypted)[0:1337], pub=False)
    logfile = codecs.open(logfilename, "w", "utf-8")
    logfile.write(str(inmail_decrypted))
    logfile.close()

    #Export processed message
    exportfilename = os.path.join(settings["exportpath"], "in." + settings["mode"] + ".processed.eml")
    dbg("Export planck-processed message: " + c(exportfilename, 6))
    exportfile = codecs.open(exportfilename, "w", "utf-8")
    exportfile.write(str(inmail_decrypted))
    exportfile.close()



# ### Scan pipeline #################################################################################


def filter_message(message):
    """
    Run all the commands on the settings['scan_pipes'] for the decrypted message

    Args:
        message (Message):  an instance of the Message class.

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
            msgtoscan = str(message.inmail_decrypted)
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
            dbg(f"Scanner {name} not available: {rc}", log_level="ERROR")

        if rc in desc.keys():
            scanresults[name] = rc
            dbg("Result: " + c(desc[rc], cols[rc]))
        else:
            dbg("Unknown return code for scanner " + name + ": " + rc, log_level="ERROR")

        if rc == 2:
            dbg(f"Error detected with scanner {name}", log_level="ERROR")
            exit(11)

        if stdout and len(stdout) > 0:
            dbg(c("STDOUT:\n", 2) + prettytable(stdout.decode("utf8").strip().split("\n")))
        if stderr and len(stderr) > 0:
            dbg(c("STDERR:\n", 1) + prettytable(stderr.decode("utf8").strip().split("\n")))
            # dbg("Return code: " + c(str(rc), 3));

    dbg("Combined scan results:\n" + prettytable(scanresults))

    if sum(scanresults.values()) == 0:
        dbg("All scans " + c("PASSED", 2) + ", relaying message", 2, log_level="INFO")
    else:
        dbg("Some scans " + c("FAILED", 1) + ", not relaying message (keeping it in the Postfix queue for now)", log_level="WARNING")
        admin_msg = f"A message from {message.msgfrom} and to {message.msgto} failed some of the scans."
        dbgmail(msg=admin_msg, subject="planck Proxy Scan failure")
        # sender_msg = f"Your message could not be delivered to {message.msg['msgto']}
        # because it failed some of our scans."
        # failurescanmail(sender_msg, message.msg['msgfrom'])
        exit(1)  # keep message on hold


def deliver_mail(message):
    """
    Send outgoing mail

    Args:
        message (Message):  an instance of the Message class.

    Returns:
        None

    """
    from_username = message.inmail_parsed.from_.username
    from_address = message.inmail_parsed.from_.address

    from_username_part = c(from_username, 2) if from_username and len(from_username) > 0 else ""
    from_address_part = c(" <" + from_address + ">", 3)

    to_address_part = c(" <" + message.msgto + ">", 3)

    dbg("Sending mail")
    dbg(f"From: {from_username_part}{from_address_part}")
    dbg(f"  To: {to_address_part}")


    sendmail(message.inmail, recipient=message.msgto)

    dbg("===== " + c("planck Proxy ended", 2) + " =====", log_level="INFO")
