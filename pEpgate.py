#!/usr/bin/env -S python3 -B

import os
import io
import re
import sys
import html
import json
import email
import base64
import argparse
import atexit
import codecs
import random
import socket
import smtplib
import traceback

from glob        import glob
from uuid        import uuid4
from time        import sleep
from shutil      import copytree
from datetime    import datetime
from subprocess  import Popen, PIPE, STDOUT
from collections import OrderedDict

from settings    import *
from pEphelpers  import *

### Parse args ####################################################################################

def get_default(setting):
	"""
	Get the default value for the given setting with the following priority:
	1. Env variable
	2. String on settings.py file (aka vars loaded into the memory space)
	"""
	env_val = os.getenv(setting)
	if env_val:
		return env_val
	settings_vars = globals()
	settings_val = settings_vars.get(setting)
	return settings_val

parser = argparse.ArgumentParser(description='pEp Proxy CLI.')
parser.add_argument('mode', choices=["encrypt", "decrypt"], help='Mode')
parser.add_argument('--DEBUG', action='store_true',
	default=get_default("DEBUG"), help=f'Set DEBUG mode, default is {get_default("DEBUG")}')
parser.add_argument('--EXTRA_KEYS', nargs='*', default=get_default("EXTRA_KEYS"),
	help=f'Space-separated fingerprint(s) to use as extra key(s) when encrypting messages, default is "{get_default("EXTRA_KEYS")}"')
parser.add_argument('--keys_dir', default=get_default("keys_dir"),
	help=f'Directory where the extra key should be imported from, default is "{get_default("keys_dir")}"')
parser.add_argument('--work_dir', default=get_default("work_dir"),
	help=f'Directory where the command outputs are placed, default is "{get_default("work_dir")}"')
parser.add_argument('--SMTP_HOST', default=get_default("SMTP_HOST"),
	help=f'Address of the SMTP host used to send the messages. Default "{get_default("SMTP_HOST")}"')
parser.add_argument('--SMTP_PORT', type=int, default=get_default("SMTP_PORT"),
	help=f'Port of the SMTP host used to send the messages. Default "{get_default("SMTP_PORT")}"')

args = parser.parse_args()
for key,val in vars(args).items():
	# Dump the args dict into the namespace so settings can be overwritten
	globals()[key] = val

### Exception / post-execution handling ###########################################################

def except_hook(type, value, tback):
	dbg(c("!!! pEp Gate - Unhandled exception !!!", 1))
	mailcontent = ""
	for line in traceback.format_exception(type, value, tback):
		dbg(line.strip())
		mailcontent += line
	dbgmail(mailcontent)
	exit(31)

def cleanup():
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

### Global vars / Initialization ##################################################################

# Postfix sets this to "C" by default, we want full Unicode support though
os.environ['LANG'] = os.environ['LC_ALL'] = "en_US.UTF-8"
home               = os.path.dirname(__file__) + "/"
gate_version       = "2.12"
locktimeout        = 60
lastactiontime     = datetime.now()
adminlog = textlog = htmllog = ""
logpath            = None
dts                = None
workdirpath        = os.path.join(home, work_dir)
keypath            = os.path.join(home, keys_dir)
logfilepath        = os.path.join(home, logfile)
fwdmappath         = os.path.join(home, forwarding_map)
usermappath        = os.path.join(home, username_map)
nextmxpath         = os.path.join(home, nextmx_map)
aliasespath        = os.path.join(home, aliases_map)
lockfilepath       = os.path.join(home, "pEpGate.lock")
sys.excepthook     = except_hook
inmail             = ""

atexit.register(cleanup)

if __name__ == "__main__":
	import pEpgatemain
