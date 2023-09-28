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
import subprocess

from glob import glob
from subprocess import Popen, PIPE, STDOUT

from .printers import dbg, c

from proxy.proxy_settings import settings


def is_sq_installed(sq_bin):
    try:
        subprocess.run([sq_bin, "-h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except Exception:
        return False


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
    run_sq = False
    sq_bin = settings["sq_bin"]
    if is_sq_installed(sq_bin):
        run_sq = True

    db = sqlite3.connect(os.path.join(os.environ["HOME"], settings["database_folder"], "keys.db"))

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
        if run_sq:
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

        else:
            inspected = {"is_private": "N/A", "sq_inspect": "N/A"}

        allkeys += [{"pEp_keys.db": fromdb, "key_blob": inspected}]

    db.close()

    if len(allkeys) > 0:
        return allkeys
    else:
        return False
