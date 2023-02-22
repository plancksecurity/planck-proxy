#!/usr/bin/python3

import sqlite3
import sys

def delete_key(keyring, address, work_dir):
    """Takes keyring, address and workdir and deletes address from the keyring."""

    print("Deleting key(s) of address " + address + " from keyring " + keyring)

    def collate_email(a, b):
        return 1 if a > b else -1 if a < b else 0

    ### keys.db
    db = sqlite3.connect(work_dir + "/" + keyring + "/.pEp/keys.db")
    db.create_collation("EMAIL", collate_email)

    q = db.execute("SELECT * FROM userids WHERE userid = ?;", (address,))
    for r in q:
        print("== " + r[0] + " -> " + r[1])

        d = db.execute("DELETE FROM subkeys WHERE primary_key = ?;", (r[1],))
        print("Removed subkeys: " + str(d.rowcount))

        d = db.execute("DELETE FROM keys WHERE primary_key = ?;", (r[1],))
        print("   Removed keys: " + str(d.rowcount))

        d = db.execute("DELETE FROM userids WHERE userid = ?;", (r[0],))
        print("Removed userids: " + str(d.rowcount))

    db.commit()

    ### management.db
    db = sqlite3.connect(work_dir + "/" + keyring + "/.pEp/management.db")

    d = db.execute("DELETE FROM trust WHERE user_id = ?;", ("TOFU_" + address,))
    print("Removed trust tofu: " + str(d.rowcount))

    d = db.execute("DELETE FROM person WHERE id = ?;", ("TOFU_" + address,))
    print("Removed person tofu: " + str(d.rowcount))

    d = db.execute("DELETE FROM identity WHERE address = ?;", (address,))
    print("Removed identity: " + str(d.rowcount))

    db.commit()


if __name__ == '__main__':
    import argparse

    #Parse args
    parser = argparse.ArgumentParser(usage='delete.key.from.keyring.py alice@pep.security bob@pep.security --WORK_DIR ~/work_dir', description='Delete a user key from another user\'s DataBase')
    parser.add_argument('keyring', help='Email of user whose DB to delete from')
    parser.add_argument('address', help='Email of user whose key to delete')
    parser.add_argument('--WORK_DIR', default='work', help='Location of the work folder')

    args = parser.parse_args()

    #Extract params and add into input vars for the fuction
    keyring = args.keyring
    address = args.address
    work_dir = args.WORK_DIR

    if work_dir.endswith("/"):
        work_dir = work_dir[:-1]
    
    delete_key(keyring, address, work_dir)