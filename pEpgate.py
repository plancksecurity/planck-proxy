#!/usr/bin/env -S python3 -B

import os
import io
import re
import sys
import html
import json
import email
import base64
import atexit
import codecs
import random
import socket
import traceback

from glob        import glob
from uuid        import uuid4
from time        import sleep
from shutil      import copytree
from datetime    import datetime
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
lockfilepath = home + "pEpgate.lock"
testmailglob = home + "tests/*.eml"
statickpath  = home + "keys.static/"
globalkpath  = home + "keys.global/"
dbgrcpt      = "aw@pep.security"
gateversion  = "2.11"
locktimeout  = 60

# Sender domains that get a debug log when the original message had enabled "Return receipt"
dtsdomains   = ["peptest.ch", "pep.security", "0x3d.lu"]

# Senders that are allowed to use the inline-command RESETKEY/KEYRESET
resetsenders = ["support@pep.security", "contact@pep.security", "it@pep.security"]

# Never send encrypted to these domains
bldomains    = ["apple.com"]

### Extra configuration / workarounds for being called by Postfix #################################

# p≡p engine stores its management database in $HOME which Postfix does not set by itself
os.environ['HOME'] = home

# Postfix sets language to "C" by default so we also need to override these to allow special characters in the output
os.environ['LANG'] = os.environ['LC_ALL'] = "en_US.UTF-8"

### Helper functions ##############################################################################

def dbg(text, printtiming=False, pub=True):
	global logfilepath, adminlog, textlog, htmllog, lastactiontime, thisactiontime
	thisactiontime = datetime.now()
	took = (thisactiontime - lastactiontime).total_seconds()
	lastactiontime = thisactiontime

	if len(text) == 0: # don't output anything, only time the next event
		return took

	# text = c(str(os.getpid()).rjust(5, " "), 5) + " | " +
	text = c(thisactiontime.strftime('%d.%m.%Y %H:%M:%S.%f'), 3) + " " + str(text) \
		+ (" " + c("{:1.6f}".format(took) + "s", 5) if printtiming else "")

	# Unconditionally write to the global logfile
	with codecs.open(logfilepath, "a+", "utf-8") as d:
		d.write(c(str(os.getpid()), 5) + " | " + text + "\n")
	d.close()

	if sys.stdout.isatty():
		print(text)

	adminlog += toplain(text) + "\n"
	textlog += text + "\n"

	if pub:
		htmllog += tohtml(text) + "<br>\n"

	return took

def c(text, color=0):
	return '\033[1;3' + str(color) + 'm' + text + '\033[1;m'

def toplain(text):
	ret = text
	ret = ret.replace('\033[1;30m', '')
	ret = ret.replace('\033[1;31m', '')
	ret = ret.replace('\033[1;32m', '')
	ret = ret.replace('\033[1;33m', '')
	ret = ret.replace('\033[1;34m', '')
	ret = ret.replace('\033[1;35m', '')
	ret = ret.replace('\033[1;36m', '')
	ret = ret.replace('\033[1;37m', '')
	ret = ret.replace('\033[1;m', '')
	return ret

def tohtml(text):
	ret = text
	ret = html.escape(ret, True)
	ret = ret.replace('\n', '<br>\n')
	ret = ret.replace(' ', '&nbsp;')
	ret = ret.replace('\033[1;30m', '<font color="#000000">') # black
	ret = ret.replace('\033[1;31m', '<font color="#ff0000">') # red
	ret = ret.replace('\033[1;32m', '<font color="#00bb00">') # green
	ret = ret.replace('\033[1;33m', '<font color="#ff8800">') # yellow
	ret = ret.replace('\033[1;34m', '<font color="#0000ff">') # blue
	ret = ret.replace('\033[1;35m', '<font color="#ff00ff">') # pink
	ret = ret.replace('\033[1;36m', '<font color="#5555ff">') # bright-blue
	ret = ret.replace('\033[1;37m', '<font color="#666666">') # white
	ret = ret.replace('\033[1;m', '</font>')
	return ret

def getlog(type):
	return globals()[type] if type in ["textlog", "htmllog"] else ""

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
		return True
	else:
		dbg(c("ERROR 6 - Mail could not be sent, return code: " + str(retval), 1))
		dbg("sendmail's stdout:")
		for line in p.stdout:
			dbg(line)
		return False

def dbgmail(msg, rcpt=dbgrcpt, subject="[FATAL] pEp Gate @ " + socket.getfqdn() + " crashed!", attachments=[]):
	dbg("Sending message to " + c(rcpt, 2) + ", subject: " + c(subject, 3))

	if len(attachments) == 0:
		mailcontent  = "Content-type: text/html; charset=UTF-8\n"
	else:
		mailcontent  = "Content-Type: multipart/mixed; boundary=\"pEpMIME\"\n"

	mailcontent += "From: pepgate@" + socket.getfqdn() + "\n"
	mailcontent += "To: " + rcpt + "\n"
	mailcontent += "Subject: " + subject + "\n\n"

	if len(attachments) > 0:
		mailcontent += "This is a multi-part message in MIME format.\n"
		mailcontent += "--pEpMIME\n"
		mailcontent += "Content-Type: text/html; charset=UTF-8\n"
		mailcontent += "Content-Transfer-Encoding: 7bit\n\n"

	mailcontent += '<html><head><style>'
	mailcontent += '.console { font-family: Courier New; font-size: 13px; line-height: 14px; width: 100%; }'
	mailcontent += '</style></head>'
	mailcontent += '<body topmargin="0" leftmargin="0" marginwidth="0" marginheight="0"><table class="console"><tr><td>'
	mailcontent += (msg + "<br>" + ("=" * 80) + "<br><br>" if len(msg) > 0 else "") + htmllog
	mailcontent += '</td></tr></table></body></html>'

	if len(attachments) > 0:
		for att in attachments:
			dbg("Attaching " + att)

			mailcontent += "\n\n--pEpMIME\n"
			mailcontent += "Content-Type: application/octet-stream; name=\"" + os.path.basename(att) + "\"\n"
			mailcontent += "Content-Disposition: attachment; filename=\"" + os.path.basename(att) + "\"\n"
			mailcontent += "Content-Transfer-Encoding: base64\n\n"

			with open(att, "rb") as f:
				mailcontent += base64.b64encode(f.read()).decode()

		mailcontent += "--pEpMIME--"

	sendmail(mailcontent)

def except_hook(type, value, tback):
	dbg(c("!!! pEp Gate - Unhandled exception !!!", 1))
	mailcontent = ""
	for line in traceback.format_exception(type, value, tback):
		dbg(line.strip())
		mailcontent += line
	dbgmail(mailcontent)
	exit(31)

# Set variables in the outer scope from within the inner scope "pEpgatemain" (mainly used in cleanup())
def setoutervar(var, val):
	globals()[var] = val

def cleanup():
	global wdp
	if dts is not None:
		attachments = []
		if logpath is not None:
			for a in glob(os.path.join(logpath, "*.eml")):
				attachments += [ a ]
		dbgmail("As requested via activated Return Receipt here's your debug log:", dts, "[DEBUG LOG] pEp Gate @ " + socket.getfqdn(), attachments)

	if os.path.isfile(lockfilepath):
		try:
			os.remove(lockfilepath)
			dbg("Lockfile " + c(lockfilepath, 6) + " removed", pub=False)
		except:
			dbg("Can't remove Lockfile " + c(lockfilepath, 6), pub=False)

### pEp Sync & echo protocol handling (TODO) ##################################

def messageToSend(msg):
	dbg("Ignoring message_to_send", pub=False)
	# dbg(c("messageToSend(" + str(len(str(msg))) + " Bytes)", 3))
	# dbg(str(msg))

def notifyHandshake(me, partner, signal):
	dbg("Ignoring notify_handshake", pub=False)
	# dbg("notifyHandshake(" + str(me) + ", " + str(partner) + ", " + str(signal) + ")")

### Load pEpGate ##############################################################

lastactiontime = datetime.now()
adminlog = textlog = htmllog = ""
logpath = None
dts = None

import pEpgatemain
