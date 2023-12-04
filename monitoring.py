#!/usr/bin/env -S python3 -B

from pprint import pformat

import traceback
import datetime
import imaplib
import smtplib
import codecs
import email
import time
import sys
import os

## Usage ##########################################################################################

if len(sys.argv) < 4:
	print()
	print("This is a basic Planck Proxy monitoring script which sends a message via authenticated SMTP then connects")
	print("to an IMAP server where it expects to receive a copy of the sent message within <timeout> seconds.")
	print("An alert will be mailed (via the same SMTP server) when a full roundtrip can't be established.")
	print("This script is best ran on a host external to the Proxy environment itself.")
	print()
	print(f"Usage: {sys.argv[0]} <SMTP hostname> <SMTP username> <SMTP password>")
	print()
	print("Cron example:")
	print("*/10 * * * * /path/to/monitoring.py smtp.office365.com 'alice@company.tld' 'password'")
	print()
	exit(1)

### Settings ######################################################################################

admin_addr  = "admin@company.tld"
sender_addr = "smtp2imap@monitoring.company.tld"
testsubject = "SMTP2IMAP monitoring"

debug	    = False
timeout	    = 60

smtp_host   = sys.argv[1]
smtp_addr   = sys.argv[2]
smtp_user   = sys.argv[2]
smtp_pass   = sys.argv[3]
smtp_tls	= True
smtp_port	= 587

imap_host   = "imap.company.tld"
imap_addr   = "dummyuser@company.tld"
imap_user   = "dummyuser"
imap_pass   = "secr3t"
imap_port	= 993

### Helpers #######################################################################################

def except_hook(type, value, tback):
	global adminlog
	mailcontent = ""
	for line in traceback.format_exception(type, value, tback):
		dbg(line.strip())
		mailcontent += line
	mailcontent += "\n" + adminlog
	sendmail(f"[FATAL] {testsubject} crashed!", mailcontent)

def sendmail(subject, body, sender=smtp_addr, recipient=admin_addr):
	mailcontent = f"Content-type: text/plain; charset=utf8\nFrom: {sender}\nTo:{recipient}\nSubject: {subject}\n\n{body}"
	conn = smtplib.SMTP(smtp_host, smtp_port)
	if debug:    conn.set_debuglevel(2)
	if smtp_tls: conn.starttls()
	conn.login(smtp_user, smtp_pass)
	conn.sendmail(smtp_addr, recipient, mailcontent)
	dbg(f"Mail with subject {c(subject, 5)} sent to {c(recipient, 2)} via host {c(smtp_host,3)}:\n{c(mailcontent, 6)}")

def dbg(text):
	global adminlog
	text = plain = f"{c(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S.%f'), 3)} {text}"

	for i in range(30,40): # strip ANSI color sequences back out for sending in plaintext mails
		plain = plain.replace(f"\033[1;{i}m", "")
	plain = plain.replace("\033[1;m", "")
	adminlog += plain + "\n"

	with codecs.open(os.path.join(os.getcwd(), "debug.log"), "a+", "utf-8") as d:
		d.write(c(str(os.getpid()), 5) + " | " + text + "\n")

	if sys.stdout.isatty():
		print(text)
		sys.stdout.flush()

def c(text, color=0, close=True):
	return '\033[1;3' + str(color) + 'm' + text + '\033[1;m'

### Main ##########################################################################################

sys.excepthook = except_hook
adminlog = ""
lastactiontime = datetime.datetime.now()
testtimesent = round(time.time() * 1000)
sendmail(testsubject, str(testtimesent), smtp_addr, imap_addr)

conn = imaplib.IMAP4_SSL(imap_host, 993)
if debug:
	conn.debug = 4
conn.login(imap_user, imap_pass)
conn.select("Inbox", False)

tryuntil = time.time() + timeout

dbg(f"Connected via IMAP to mailbox {c(imap_user, 2)} on host {c(imap_host, 5)}. Waiting for sent message to loop back...")

testmailfound = False
oldscanned = False

while time.time() < tryuntil and not testmailfound:
	tmp, data = conn.uid("SEARCH", "SUBJECT \"" + testsubject + "\"")
	oldscanned = True

	print("{:2.2f} ".format(tryuntil - time.time()), end="")
	sys.stdout.flush()

	if debug:
		dbg(f"SEARCH: {data}")

	for uid in data[0].split():
		tmp, data = conn.uid("FETCH", uid, "(FLAGS RFC822.HEADER)") # use ".HEADER" so non-SMTP2IMAPMon-messages remain unread
		try:
			mail = data[-2][1].decode("utf8")
			if debug:
				dbg(f"Headers of mail UID {c(uid.decode(),3)}:\n{c(mail,5)}")

			subject = email.message_from_string(mail).get_all("Subject")[0]
			if debug:
				dbg(f"Subject: {c(subject, 5)}")

			if testsubject in subject:
				if debug:
					dbg("=== Found a message with a test subject ===")
				tmp, data = conn.uid("FETCH", uid, "(FLAGS RFC822)") # FETCH again without the ".HEADER" suffix
				mail = data[-2][1].decode("utf8")

				if debug:
					dbg(f"Full mail UID {c(uid.decode(),3)}:\n{c(mail,5)}")

				if str(testtimesent) in mail:
					testmailfound = True
					print("")
					dbg("[UID: " + uid.decode("utf8") + "] Testmail loop took {:2.3f} s".format((time.time() * 1000 - testtimesent) / 1000))
					conn.uid("STORE", uid, "+FLAGS", "(\Deleted)")
					conn.expunge()
					exit(0)
				else:
					dbg("[UID: " + uid.decode("utf8") + "] Old testmail, deleting...")
					dbg("DATA: " + str(data))
					conn.uid("STORE", uid, "+FLAGS", "(\Deleted)")
					conn.expunge()
		except Exception as e:
			dbg("Exception in IMAP: " + str(e))

	time.sleep(0.25)

raise Exception("[!!!] Timeout waiting for message to loop back")
conn.close()
