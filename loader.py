#!/usr/bin/env -S python3 -B

import os
import io
import re
import sys
import json
import atexit
import codecs
import random
import traceback

from glob        import glob
from uuid        import uuid4
from time        import sleep
from shutil      import copytree
from datetime    import datetime
from email       import message_from_string
from subprocess  import Popen, PIPE, STDOUT
from collections import OrderedDict

### Configuration #################################################################################

home         = os.path.dirname(__file__) + "/"
fwdmappath   = home + "forwarding.map"
usermappath  = home + "username.map"
nextmxpath   = home + "nextmx.map"
aliasespath  = home + "aliases.map"
workdirpath  = home + "work/"
logfilepath  = home + "debug.log"
lockfilepath = home + "PlanckGate.lock"
testmailglob = home + "tests/*.eml"

# exportedpath = home + "keys.exported/" # TODO: remove once most/all old GnuPG keys are migrated to sq
statickpath  = home + "keys.static/"
globalkpath  = home + "keys.global/"

bldomains    = ["apple.com"]

locktimeout  = 60

### Extra configuration / workarounds for being called by Postfix #################################

# p≡p engine stores its management database in $HOME which Postfix does not set by itself
os.environ['HOME'] = home

# Postfix sets language to "C" by default so we also need to override these to allow special characters in the output
os.environ['LANG'] = os.environ['LC_ALL'] = "en_US.UTF-8"

### Helper functions ##############################################################################

def dbg(text, printtiming=False):
	global logfile, lastactiontime, thisactiontime
	thisactiontime = datetime.now()
	took = thisactiontime - lastactiontime
	lastactiontime = thisactiontime

	if len(text) == 0: # Call dbg("") to merely time events without any output
		return True

	text = c(str(os.getpid()).rjust(5, " "), 5) + " | " + c(thisactiontime.strftime('%d.%m.%Y %H:%M:%S.%f'), 3) + " " + str(text) \
		+ (" " + c(str(took.seconds) + "." + str(took.microseconds).zfill(6) + "s", 5) if printtiming else "")

	# Unconditionally write to the internal logfile
	with codecs.open(logfilepath, "a+", "utf-8") as d:
		d.write(text + "\n")
	d.close()

	if sys.stdout.isatty():
		print(text)

def c(text, color=0):
	return '\033[1;3' + str(color) + 'm' + text + '\033[1;m'


def sendmail(msg):
	# Replace dots at the beginning of a line with the MIME-encoded, quoted-printable counterpart. Fuck you very much, Outlook!
	msg = re.sub('^\.', '=2E', msg, flags=re.M)

	# dbg("Passing message to sendmail") # + c(str(out), 6))
	p = Popen(["timeout", "15", "/usr/sbin/sendmail", "-t"], shell=False, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
	p.stdin.write(msg.encode("utf8") + "\r\n.\r\n".encode("ascii"))

	p.stdin.flush()
	retval = p.wait()

	if retval == 0:
		dbg(c("Mail successfully sent", 2))
	else:
		dbg(c("ERROR 6 - Mail could not be sent, return code: " + str(retval), 1))
		dbg("sendmail's stdout:")
		for line in p.stdout:
			dbg(line)
		exit(30)

def dbgmail(msg):
	dbg(c("Sending debug message", 1))
	mailcontent  = "From: debug@gate.planck.security\n"
	mailcontent += "To: aw@planck.security\n"
	mailcontent += "Subject: [FATAL] Planck Gate barfed!\n\n"
	mailcontent += msg
	sendmail(mailcontent)

def except_hook(type, value, tback):
	dbg(c("!!! Planck Gate - Unhandled exception !!!", 1))
	mailcontent = ""
	for line in traceback.format_exception(type, value, tback):
		dbg(line.strip())
		mailcontent += line
	dbgmail(mailcontent)
	exit(31)

sys.excepthook = except_hook

lastactiontime = datetime.now()

import main
