#!/usr/bin/python3

import sqlite3
import sys

if len(sys.argv) < 3:
	print("Usage: " + sys.argv[0] + " <keyring> <address>")
	exit(1)
else:
	print("Deleting key(s) of address " + sys.argv[2] + " from keyring " + sys.argv[1])

def collate_email(a, b):
	return 1 if a > b else -1 if a < b else 0

### keys.db
db = sqlite3.connect("/home/pepgate/work/" + sys.argv[1] + "/.pEp/keys.db")
db.create_collation("EMAIL", collate_email)

q = db.execute("SELECT * FROM userids WHERE userid = ?;", (sys.argv[2],))
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
db = sqlite3.connect("/home/pepgate/work/" + sys.argv[1] + "/.pEp/management.db")

d = db.execute("DELETE FROM trust WHERE user_id = ?;", ("TOFU_" + sys.argv[2],))
print("Removed trust tofu: " + str(d.rowcount))

d = db.execute("DELETE FROM person WHERE id = ?;", ("TOFU_" + sys.argv[2],))
print("Removed person tofu: " + str(d.rowcount))

d = db.execute("DELETE FROM identity WHERE address = ?;", (sys.argv[2],))
print("Removed identity: " + str(d.rowcount))

db.commit()
