"""
cryptography.py

This module provides functions for working with cryptographic keys and PGP blobs using the Sequoia CLI tool.

Functions:
- keys_from_keyring(userid=None): Retrieves all the keys in the keyring or a specific key matching the given user ID.
- inspectusingsq(PGP): Inspects a given PGP blob using the Sequoia CLI tool.
- decryptusingsq(inmail, secretkeyglob): Decrypts a PGP message using the Sequoia CLI tool.
"""

import sqlite3
import os
import re
import io
import tempfile

from glob import glob
from subprocess import Popen, PIPE, STDOUT

from .printers import dbg, c

from proxy_settings import settings


def keys_from_keyring(userid=None):
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
            sqkeyfile = ("sec" if r3[1] is True else "pub") + "." + r1[0] + "." + r1[1] + ".key"
            open(sqkeyfile, "wb").write(r3[0])
            cmd = [sq_bin, "enarmor", sqkeyfile, "-o", sqkeyfile + ".asc"]
            p = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)  # stderr=STDOUT for debugging
            ret = p.wait()

            cmd = [sq_bin, "inspect", "--certifications", sqkeyfile]
            p = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)  # stderr=STDOUT for debugging
            ret = p.wait()

            if ret == 0:
                inspected = {}
                inspected["is_private"] = r3[1]
                inspected["sq_inspect"] = []
                for line in io.TextIOWrapper(p.stdout, encoding="utf-8", errors="strict"):
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
                        inspected["username"] = patt.findall("\n".join(inspected["sq_inspect"]))[0]
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
    keyused = None

    dbg(c("[!] Fallback-decrypting via sq CLI tool", 1))

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

            if rc == 0:
                keyused = [re.search(r"[0-9a-zA-Z]{40}", secretkey)[0]]
                break

        os.unlink(tmppath)

        if len(stdout) > 0:
            patt = re.compile(r"Message-ID:.*?^$", re.MULTILINE | re.DOTALL)
            pepparts = patt.findall(stdout.decode("utf8"))
            ret += "\n".join(pepparts)

    return [ret.replace("X-pEp-Wrapped-Message-Info: INNER\r\n", ""), keyused]
