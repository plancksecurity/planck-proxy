import os
import sys
import re
import codecs
import importlib
import traceback

from time import sleep
from datetime import datetime
from glob import glob
from subprocess import Popen, PIPE

from pEpgatesettings import settings
from pEphelpers import (
    dbg,
    c,
    prettytable,
    cleanup,
    get_contact_info,
    getmailheaders,
    jsonlookup,
    messageToSend,
    notifyHandshake,
    keysfromkeyring,
    dbgmail,
    decryptusingsq,
    sendmail,
    getlog,
)


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
                            'msg', 'us' and 'them' dictionaries.

    Returns:
        None.
    """

    msgfrom, msgto = get_contact_info(message.msg["inmail"])

    message.msg["msgfrom"] = msgfrom
    message.msg["msgto"] = msgto

    message.them["addr"] = msgfrom
    message.us["addr"] = msgto


def enable_dts(message):
    """
    If sender enabled "Return receipt" and is part of the dts_domains setting,
    allow cleanup() to send back debugging info

    Args:
        message (Message): an instance of the Message class containing the parsed message
                            in the 'msg' dictionary.

    Returns:
        None

    """
    global settings
    dts = getmailheaders(message.msg["inmail"], "Disposition-Notification-To")  # Debug To Sender

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


# ### Address- & domain-rewriting (for asymmetric inbound/outbound domains) #########################


# def addr_domain_rewrite(message):
#     """
#     Address- & domain-rewriting (for asymmetric inbound/outbound domains)

#     Args:
#         message (Message): an instance of the Message class containing 'us' dictionary.

#     Returns:
#         None
#     """

#     forwarding_map_path = os.path.join(settings["home"], settings["forwarding_map"])
#     rewrite = jsonlookup(forwarding_map_path, message.us["addr"], False)
#     if rewrite is not None:
#         dbg("Rewriting our address from " + c(message.us["addr"], 1) + " to " + c(rewrite, 3))
#         message.us["addr"] = rewrite
#     else:
#         ourdomain = message.us["addr"][message.us["addr"].rfind("@") :]
#         rewrite = jsonlookup(forwarding_map_path, ourdomain, False)
#         if rewrite is not None:
#             dbg("Rewriting domain of message from " + c(ourdomain, 3) + " to " + c(rewrite, 1))
#             message.us["addr"] = message.us["addr"].replace(ourdomain, rewrite)


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
    workdirpath = os.path.join(settings["home"], settings["work_dir"], message.us["addr"])
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


# ### Summary #######################################################################################


def print_summary_info(message):
    """
    Print summary information about the message and whether initial import is required

    Args:
        message (Message):  an instance of the Message class containing the 'msg' dictionary.

    Returns:
        None
    """

    dbg("       Message from: " + c(str(message.msg["msgfrom"]), 5))
    dbg("         Message to: " + c(str(message.msg["msgto"]), 5))
    dbg("        Our address: " + c(message.us["addr"], 3))
    dbg("      Their address: " + c(message.them["addr"], 3))
    dbg("    Initital import: " + ("Yes" if check_initial_import() else "No"))


# ### Logging #######################################################################################


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


# ### Load p≡p ######################################################################################


def load_pep():
    """
    Import the p≡p engine. This will create the .pEp folder in the current $HOME
    This method should never be called before init_workdir

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


# ### Show me what you got ##########################################################################


def print_keys_and_headers(message):
    """
    Print environment variables, keys in the keyring and headers in original message.

    Args:
        message (Message):  an instance of the Message class containing the 'msg' dictionary.

    Returns:
        None.
    """
    dbg(
        c("┌ Environment variables", 5) + "\n" + prettytable(os.environ),
        pub=False,
    )
    dbg(c("┌ Keys in this keyring (as stored in keys.db)", 5) + "\n" + prettytable(keysfromkeyring()))
    dbg(
        c("┌ Headers in original message (as seen by non-p≡p clients)", 5)
        + "\n"
        + prettytable(getmailheaders(message.msg["inmail"]))
    )


# ### Check if we have a private key for "us" #######################################################


# def check_sender_privkey(message):
#     """
#     Check if we have a private key for the sender

#     Args:
#         message (Message):  an instance of the Message class containing the 'us' dictionary.

#     Returns:
#         None
#     """
#     ourkey = keysfromkeyring(message.us["addr"])
#     if ourkey is False:
#         dbg("No private key for our address " + c(message.us["addr"], 3) + ", p≡p will have to generate one later")
#         ourkeyname = ourkeyaddr = ourkeyfpr = None
#     else:
#         dbg(
#             c("Found existing private key for our address ", 2) + c(message.us["addr"], 5) + ":\n"
#               + prettytable(ourkey)
#         )
#         # TODO: this doesn't support multiple UID's per key, we should figure out the most recent one
#         ourkeyname = ourkey[0]["key_blob"]["username"]
#         ourkeyaddr = ourkey[0]["pEp_keys.db"]["UserID"]
#         ourkeyfpr = ourkey[0]["pEp_keys.db"]["KeyID"]
#         dbg("Our key name: " + ourkeyname)
#         dbg("Our key addr: " + ourkeyaddr)
#         dbg("Our key fpr:  " + ourkeyfpr)

#         message.us["keyname"] = ourkeyname
#         message.us["keyaddr"] = ourkeyaddr
#         message.us["keyfpr"] = ourkeyfpr


# ### Create/set own identity ######################################################################
# def set_own_identity(pEp, message):
#     """
#     Create or set our own p≡p identity

#     Args:
#         pEp (module): The p≡p engine module object.
#         message (Message):  an instance of the Message class containing the 'us' and 'them' dictionaries.

#     Returns:
#         None
#     """
#     username_map_path = os.path.join(settings["home"], settings["username_map"])
#     ourname = jsonlookup(username_map_path, message.us["addr"], False)

#     if message.us["keyname"] is None and message.us["keyaddr"] is None and message.us["keyfpr"] is None:
#         dbg(c("No existing key found, letting p≡p generate one", 3))
#         if ourname is None:
#             import re

#             ourname = re.sub(r"\@", " at ", message.us["addr"])
#             ourname = re.sub(r"\.", " dot ", ourname)
#             ourname = re.sub(r"\W+", " ", ourname)
#             dbg(
#                 c("No matching name found", 1)
#                 + " for address "
#                 + c(message.us["addr"], 3)
#                 + ", using de-@'ed address as name: "
#                 + c(ourname, 5)
#             )
#         else:
#             dbg("Found name matching our address " + c(message.us["addr"], 3) + ": " + c(ourname, 2))

#         i = pEp.Identity(message.us["addr"], ourname)
#         pEp.myself(i)
#         # redundancy needed since we can't use myself'ed or update'd keys in pEp.Message.[to|from]
#         ourpepid = pEp.Identity(message.us["addr"], ourname)
#     else:
#         dbg(c("Found existing key, p≡p will import/use it", 2))
#         if ourname is not None and ourname != message.us["keyname"]:
#             dbg(
#                 c(
#                     "Name inside existing key ("
#                     + message.us["keyname"]
#                     + ") differs from the one found in username.map ("
#                     + ourname
#                     + "), using the latter",
#                     3,
#                 )
#             )
#             i = pEp.Identity(message.us["keyaddr"], ourname)
#             # redundancy needed since we can't use myself'ed or update'd keys in pEp.Message.[to|from]
#             ourpepid = pEp.Identity(message.us["keyaddr"], ourname)
#         else:
#             i = pEp.Identity(message.us["keyaddr"], message.us["keyname"])
#             # redundancy needed since we can't use myself'ed or update'd keys in pEp.Message.[to|from]
#             ourpepid = pEp.Identity(message.us["keyaddr"], message.us["keyname"])

#         i.fpr = message.us["keyfpr"]

#     message.us["pepid"] = ourpepid


# ### Prepare message for processing by p≡p #########################################################


def create_pEp_message(pEp, message):
    """
    Create a p≡p message object and store it in the message.msg['src'] key.

    Args:
        pEp (module): The p≡p engine module object.
        message (Message):  an instance of the Message class containing the 'msg', 'us' and 'them' dictionaries.

    Returns:
        None
    """
    try:
        src = pEp.Message(message.msg["inmail"])

        # if settings["mode"] == "decrypt":
        # src.to = [message.us["pepid"]]
        # TODO: implement proper echo-protocol handling
        # src.recv_by = message.us["pepid"]

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
        message (Message):  an instance of the Message class containing the 'msg', 'us' and 'them' dictionaries.

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
                # Lower the (potentially rewritten) outer recipient back into the inner message
                # dst.to = [message.us["pepid"]]
            else:
                dbg(c("Decrypting message via Sequoia...", 2))
                tmp = decryptusingsq(
                    message.msg["inmail"],
                    os.path.join(settings["work_dir"], "sec.*.key"),
                )
                dst, keys, rating = (
                    pEp.Message(tmp[0]),
                    tmp[1],
                    None,
                )
                dbg(c("Decrypted in", 2), True)

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

            if keys is None or len(keys) == 0:
                dbg(c("Original message was NOT encrypted", 1))
                # TODO: add policy setting to enforce inbound encryption (allow/deny-list?)
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


# def add_routing_and_headers(pEp, message):
#     """
#     Complete mail headers with MX routing snd version information

#     Args:
#         pEp (module): The p≡p engine module object.
#         message (Message):  an instance of the Message class containing the 'msg', 'us' and 'them' dictionaries.

#     Returns:
#         None

#     """
#     global settings
#     settings["nextmx"] = None
#     opts = {
#         "X-pEpGate-mode": settings["mode"],
#         "X-pEpGate-version": settings["gate_version"],
#         "X-pEpEngine-version": pEp.engine_version,
#         "X-NextMX": "auto",
#     }

#     nextmx_path = os.path.join(settings["home"], settings["nextmx_map"])

#     if settings["mode"] == "decrypt":
#         nextmx = jsonlookup(
#             nextmx_path,
#             message.us["pepid"].address[message.us["pepid"].address.rfind("@") + 1 :],
#             False,
#         )

#     if nextmx is not None:
#         settings["netmx"] = nextmx
#         dbg(c("Overriding next MX: " + nextmx, 3))
#         opts["X-NextMX"] = nextmx

#     opts.update(message.msg["dst"].opt_fields)
#     message.msg["dst"].opt_fields = opts

#     if settings["DEBUG"]:
#         dbg(
#             "Optional headers:\n" + prettytable(message.msg["dst"].opt_fields),
#             pub=False,
#         )

#     dst = str(message.msg["dst"])
#     message.msg["dst"] = dst

#     # Log processed message
#     logfilename = os.path.join(settings["logpath"], "in." + settings["mode"] + ".processed.eml")
#     dbg("p≡p-processed message: " + c(logfilename, 6) + "\n" + str(dst)[0:1337])
#     logfile = codecs.open(logfilename, "w", "utf-8")
#     logfile.write(dst)
#     logfile.close()


def deliver_mail(message):
    """
    Send outgoing mail

    Args:
        message (Message):  an instance of the Message class containing the 'msg' dictionary.

    Returns:
        None

    """
    settings["nextmx"] = None
    dbg("Sending mail via MX: " + (c("auto", 3) if settings["nextmx"] is None else c(str(settings["nextmx"]), 1)))
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
        # sendmail(message.msg["dst"])
        sendmail(message.msg["inmail"])

    dbg("===== " + c("p≡pGate ended", 1) + " =====")


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
