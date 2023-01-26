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

home         = os.path.dirname(__file__) + "/"
workdirpath  = os.path.join(home, work_dir)
keypath      = os.path.join(home, keys_dir)
logfilepath  = os.path.join(home, logfile)
fwdmappath   = os.path.join(home, forwarding_map)
usermappath  = os.path.join(home, username_map)
nextmxpath   = os.path.join(home, nextmx_map)
aliasespath  = os.path.join(home, aliases_map)

gate_version = "2.12"

# We've solved the SQLite concurrency in the engine so lockfiles should soon be droppable altogether
lockfilepath = os.path.join(home, "pEpGate.lock")
locktimeout  = 60

# For testing only so not needed in settings.py
testmailglob = os.path.join(home, "tests/emails/*.eml")

# Postfix sets this to "C" by default, we want full Unicode support though
os.environ['LANG'] = os.environ['LC_ALL'] = "en_US.UTF-8"

lastactiontime = datetime.now()
adminlog = textlog = htmllog = ""
logpath = None
dts = None

if __name__ == "__main__":
	import pEpgatemain
