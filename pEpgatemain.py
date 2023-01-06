#!/usr/bin/env python3

from pEpgate import *

### More helper functions #########################################################################

def prettytable(thing, colwidth=26):
	ret = ""
	if not isinstance(thing, list):
		thing = [thing]

	for subthing in thing:
		if isinstance(subthing, str):
			ret += (" " * colwidth) + c(" | ", 5) + subthing + "\n"
		elif (hasattr(subthing, '__iter__')):
			for k, v in subthing.items():
				w = []
				keys = []

				if isinstance(v, dict) or isinstance(v, OrderedDict):
					maxkeylength = max(len(x) for x in v.keys())
					w += [ prettytable(v, max(maxkeylength, 10)) ]
					v = "\n".join(w)

				if isinstance(v, list):
					# Iterate over list to figure out if we have dicts underneath + it's max key length
					maxkeylength = colwidth
					for item in v:
						if isinstance(item, dict) or isinstance(item, OrderedDict):
							keys += item.keys()

					if len(keys) > 0:
						maxkeylength = max(len(x) for x in keys)

					if len(v) == 0:
						w = [ "None" ]

					# Iterate another round with the known max key length, call prettytable() recursively for "sub-tables"
					for item in v:
						if isinstance(item, dict) or isinstance(item, OrderedDict):
							w += [ prettytable(item, max(maxkeylength, 10)) ]
						else:
							w += [ item ]
					v = "\n".join(w)

				ret += c(str(k).rjust(colwidth), 6) + c(" | ", 5) + str(v).replace("\n", "\n" + (" " * colwidth) + c(" | ", 5)) + "\n"

		else:
			dbg("Don't know how to prettyprint this thing. Aborting!")
			sys.exit(20)

	return ret[:-1]

def keysfromkeyring(userid=None):
	global jsonout
	import sqlite3
	db = sqlite3.connect(os.environ["HOME"] + "/.pEp/keys.db")

	def collate_email(a, b):
		# dbg("collate(%s, %s)" % (a, b))
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
			subkeys += [ str(r2[0]) ]

		fromdb = {}
		fromdb["UserID"] = r1[0]
		fromdb["KeyID"] = r1[1]
		fromdb["Subkeys"] = subkeys

		q3 = db.execute("SELECT tpk, secret FROM keys WHERE primary_key = ?;", (r1[1],))
		for r3 in q3:
			sqkeyfile = ("sec" if r3[1] == True else "pub") + "." + r1[0] + "." + r1[1] + ".key"
			open(sqkeyfile, "wb").write(r3[0])
			cmd = ["/usr/local/bin/sq", "enarmor", sqkeyfile, "-o", sqkeyfile + ".asc"]
			p = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE) # stderr=STDOUT for debugging
			ret = p.wait()

			cmd = ["/usr/local/bin/sq", "inspect", "--certifications", sqkeyfile]
			p = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE) # stderr=STDOUT for debugging
			ret = p.wait()

			if ret == 0:
				inspected = {}
				inspected['is_private'] = r3[1]
				inspected['sq_inspect'] = []
				for line in io.TextIOWrapper(p.stdout, encoding="utf-8", errors="strict"):
					line = line.strip()
					inspected['sq_inspect'] += [line]

				inspected['sq_inspect'] = inspected['sq_inspect'][2:] # Hide internal filename & extra whitespace

				try:
					inspected['username'] = re.findall(r'UserID: (.*?) \<.*\r?\n?', str(inspected['sq_inspect']))[0]
				except:
					dbg("[!] No username/user ID was contained in this PGP blob. Full sq inspect:\n" + "\n".join(inspected['sq_inspect']))
					pass

		allkeys += [ { "pEp_keys.db": fromdb, "key_blob": inspected } ]

	db.close()

	if len(allkeys) > 0:
		return allkeys
	else:
		return False

def inspectusingsq(PGP):
	import tempfile
	tf = tempfile.NamedTemporaryFile()
	dbg("TMP file: " + tf.name)
	tf.write(PGP.encode("utf8"))
	cmd = ["/usr/local/bin/sq", "inspect", "--certifications", tf.name]
	p = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
	ret = p.wait()

	for line in io.TextIOWrapper(p.stdout, encoding="utf-8", errors="strict"):
		line = line.strip()
		dbg(line)

def decryptusingsq(inmail, secretkeyglob):
	ret = ""
	patt = re.compile(r"-----BEGIN PGP MESSAGE-----.*?-----END PGP MESSAGE-----", re.MULTILINE | re.DOTALL)
	pgpparts = patt.findall(inmail)

	dbg(c("[!!!] Using decryptusingsq() fallback. Attachments will be LOST!", 1))

	# dbg("Inmail: " + str(inmail))
	# dbg("PGP: " + str(pgpparts))

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

			cmd = ["/usr/local/bin/sq", "decrypt", "--secret-key-file", secretkey, "--", tmppath]
			dbg("CMD: " + " ".join(cmd))

			p = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
			stdout, stderr = p.communicate()

			# dbg("STDOUT: " + c(stdout.decode("utf8"), 2))
			# dbg("STDERR: " + c(stderr.decode("utf8"), 1))

			patt = re.compile(r"Message-ID:.*?^$", re.MULTILINE | re.DOTALL)
			pepparts = patt.findall(stdout.decode("utf8"))

			ret += "\n".join(pepparts)

		os.unlink(tmppath)

	return ret.replace("pEp-Wrapped-Message-Info: INNER\n", "")

def getmailheaders(inmsg, headername=None):
	try:
		msg = message_from_string(inmsg)
		if (headername is not None):
			headers = msg.get_all(headername)
		else:
			headers = []
			origheaders = msg.items()
			for k, v in origheaders:
				vclean = []
				for line in v.splitlines():
					vclean += [line.strip()]
				headers += [{k:"\n".join(vclean)}]
		return headers
	except:
		dbg("Can't pre-parse e-mail. Aborting!")
		e = sys.exc_info()
		dbg("ERROR 5 - " + str(e[0]) + ": " + str(e[1]))
		dbg("Traceback: " + str(traceback.format_tb(e[2])))
		return False
		exit(21)

def jsonlookup(jsonmapfile, key, bidilookup=False):
	# dbg("JSON lookup in file " + jsonmapfile + " for key " + key)

	result = None

	with open(jsonmapfile) as f:
		j = json.load(f)
	try:
		result = j[key]
		dbg(c("Forward-rewriting ", 2) + key + " to " + str(result))
	except KeyError:
		pass

	if result is None and bidilookup:
		try:
			jr = {v: k for k, v in j.items()}
			result = jr[key]
			dbg(c("Reverse-rewriting ", 3) + key + " to " + str(result))
		except KeyError:
			pass

	# dbg("== " + key[:key.rfind("@")])
	if jsonmapfile == fwdmappath and result is None and key[:key.rfind("@")] in ("root", "postmaster", "noreply", "no-reply"): # Silly debug catch-all for backscatter
		result = "andy@pep-security.net" # must use the .net alias here since Exchange doesn't like From: aw@pep.sec and To: aw@pep.sec within one and the same message
		dbg(c("Fallback-rewriting ", 2) + key + " to " + result)

	return result

### Initialization ################################################################################

sys.excepthook = except_hook
atexit.register(cleanup)

inmail = ""

### Lockfile handling #############################################################################

locktime = 0
lockpid = None

while os.path.isfile(lockfilepath) and locktime < locktimeout:
	lock = open(lockfilepath, "r")
	lockpid = lock.read()
	lock.close()
	if lockpid.isdigit() and int(lockpid) > 1:
		try:
			os.kill(int(lockpid), 0)
		except OSError:
			dbg("Lock held by dead PID " + lockpid + ", removing lockfile")
			cleanup()
			lockpid = None
		else:
			dbg("Lock held by active PID " + lockpid + ", killing in " + str(locktimeout - locktime) + "s")
	else:
		dbg("Lockfile doesn't contain any numeric PID [" + str(lockpid) + "]. Removing file")
		cleanup()
	locktime += 1
	sleep(1)

if os.path.isfile(lockfilepath) and lockpid is not None and lockpid.isdigit():
	lockpid = int(lockpid)
	if lockpid > 1:
		try:
			dbg("Sending SIGTERM to PID " + str(lockpid))
			os.kill(lockpid, 15)
			sleep(1)
			dbg("Sending SIGKILL to PID " + str(lockpid))
			os.kill(lockpid, 9)
			sleep(1)
		except:
			pass

lock = open(lockfilepath, "w")
lock.write(str(os.getpid()))
lock.close()
dbg("Lockfile created")

if len(sys.argv) < 2:
	dbg("No operation mode specified. Usage: " + sys.argv[0] + " [encrypt|decrypt]")
	exit(22)

mode = sys.argv[1]

dbg("===== " + c("p≡pgate started", 2) + " in mode " + c(mode, 3) +" | PID " + c(str(os.getpid()), 5) + " | UID " + c(str(os.getuid()), 6) + " | GID " + c(str(os.getgid()), 7) + " =====")

### Read original message from stdin or use a testmail ############################################

dbg("Reading message (to confirm press CTRL+D on an empty line)...")

inbuf = bytearray()
while True:
	part = sys.stdin.buffer.read(1024)
	if len(part) > 0:
		inbuf += part
	else:
		break

try:
	for line in inbuf.decode(encoding="utf-8", errors="strict"):
		inmail += str(line)
except:
	try:
		dbg(c("Can't decode input as utf-8, trying latin-1", 1))
		for line in inbuf.decode(encoding="latin-1", errors="strict"):
			inmail += str(line)
	except:
		dbg(c("Can't decode input as latin-1 either, doing utf-8 anyways and ignoring all errors", 1))
		for line in inbuf.decode(encoding="utf-8", errors="ignore"):
			inmail += str(line)

if len(inmail) == 0:
	dbg(c("No message was passed to me on stdin", 1))
	testmails = glob(testmailglob)
	numtestmails = len(testmails)
	if numtestmails > 0:
		testmailtouse = random.choice(testmails)
		dbg("There are " + str(numtestmails) + " testmails available, using " + c(testmailtouse, 3))
		with open(testmailtouse, "r") as f:
			for line in f:
				inmail += line
	else:
		dbg(c("No testmails available either. Aborting!", 1))
		exit(23)

### Figure out how we have been contacted, what to do next ########################################

mailparseregexes = [
	r"<([\w\-\_\"\.]+@[\w\-\_\"\.{1,}]+)>",
	r"<?([\w\-\_\"\.]+@[\w\-\_\"\.{1,}]+)>?"
]

# From, fallback: Return-Path
msgfrom = ""
try:
	for mpr in mailparseregexes:
		msgfrom = "-".join(getmailheaders(inmail, "From"))
		msgfrom = "-".join(re.findall(re.compile(mpr), msgfrom))
		if len(msgfrom) > 0:
			break
except:
	pass

if msgfrom.count("@") != 1:
	dbg(c("Unparseable From-header, falling back to using Return-Path", 1))
	for mpr in mailparseregexes:
		msgfrom = "-".join(getmailheaders(inmail, "Return-Path"))
		msgfrom = "-".join(re.findall(re.compile(mpr), msgfrom))
		if len(msgfrom) > 0:
			break

# Delivered-To, fallback if is alias: search for match in To/CC/BCC
for mpr in mailparseregexes:
	msgto = "-".join(getmailheaders(inmail, "Delivered-To"))
	msgto = "-".join(re.findall(re.compile(mpr), msgto))
	if len(msgto) > 0:
		break

aliases = jsonlookup(aliasespath, msgto, False)
if aliases is not None:
	dbg("Delivered-To is an aliased address: " + c(", ".join(aliases), 3))

	allrcpts = set()
	for hdr in ("To", "CC", "BCC"):
		try:
			for a in ", ".join(getmailheaders(inmail, hdr)).split(", "):
				for mpr in mailparseregexes:
					rcpt = " ".join(re.findall(re.compile(mpr), a))
					allrcpts.add(rcpt)
					# dbg(str(rcpt))
		except:
			# dbg("No " + hdr + " header in this message")
			pass

	dbg("All recipients / Alias candidates: " + c(", ".join(allrcpts), 5))
	for r in allrcpts:
		if r in aliases:
			dbg("Matching alias found: " + c(r, 2))
			msgto = r
			break
	else:
		dbg(c("Couldn't match alias to original Delivered-To!", 1))

if msgto.count("@") != 1:
	dbg(c("No clue how we've been contacted. Giving up...", 1))
	exit(1)

msgfrom = msgfrom.lower()
msgto = msgto.lower()

ouraddr = (msgfrom if mode == "encrypt" else msgto)
theiraddr = (msgto if mode == "encrypt" else msgfrom)

### If sender enabled "Return receipt" allow cleanup() to send back debugging info ################

dts = getmailheaders(inmail, "Disposition-Notification-To") # Debug To Sender

if dts is not None:
	dts = addr = dts[0]
	dts = "-".join(re.findall(re.compile(r"<.*@(\w{2,}\.\w{2,})>"), dts))
	dbg(c("Return receipt requested by: " + str(addr), 3))
	if dts in ("peptest.ch", "pep.security", "0x3d.lu"):
		dbg(c("Domain " + c(dts, 5) + " is whitelisted for DTS requests", 2))
		setoutervar("dts", addr)
	else:
		dbg(c("Domain is not whitelisted for DTS requests", 1))

### KEYRESET/RESETKEY command #####################################################################

keywords = ("RESETKEY", "KEYRESET")
validsenders = ("support@pep.security", "contact@pep.security", "it@pep.security")

if any(kw in inmail for kw in keywords) and mode == "encrypt" and ouraddr in validsenders and theiraddr not in validsenders:
	dbg("Resetting key for " + theiraddr + " in keyring " + ouraddr)

	for kw in keywords:
		inmail = inmail.replace(kw, "")

	cmd = [os.path.join(os.basepath(__file__), "delete.key.from.keyring.py"), ouraddr, theiraddr]
	dbg("CMD: " + " ".join(cmd))
	p = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
	stdout, stderr = p.communicate()

	dbg(c(stdout.decode("utf8"), 2))

### Address rewriting #############################################################################

if mode == "encrypt":
	nexthop = jsonlookup(fwdmappath, theiraddr, False)
	if nexthop is not None:
		dbg("Redirecting outgoing message from " + c(theiraddr, 3) + " to " + c(nexthop, 1) + ", as per forwarding.map")
		theiraddr = nexthop

if mode == "decrypt":
	nexthop = jsonlookup(fwdmappath, ouraddr, False)
	if nexthop is not None:
		dbg("Redirecting incoming message from " + c(ouraddr, 1) + " to " + c(nexthop, 3) + ", as per forwarding.map")
		ouraddr = nexthop

### Create & set working directory ################################################################

workdirpath = os.path.join(workdirpath, ouraddr)
if not os.path.exists(workdirpath):
	os.makedirs(workdirpath);

os.environ['HOME'] = workdirpath
os.chdir(workdirpath)

### Check if Sequoia-DB already exists, if not import keys later using p≡p ########################

initialimport = not os.path.exists(os.environ["HOME"] + "/.pEp/keys.db")

### Summary #######################################################################################

dbg("       Message from: " + c(str(msgfrom), 5))
dbg("         Message to: " + c(str(msgto), 5))
dbg("        Our address: " + c(ouraddr, 3))
dbg("      Their address: " + c(theiraddr, 3))
dbg("    Initital import: " + ("Yes" if initialimport else "No"))

### Logging #######################################################################################

logpath = os.path.join(workdirpath, theiraddr, datetime.now().strftime('%Y.%m.%d-%H.%M.%S.%f'))
if not os.path.exists(logpath):
	os.makedirs(logpath);

logfilename = os.path.join(logpath, "in." + mode + ".original.eml")
dbg("   Original message: " + c(logfilename, 6)) # + "\n" + inmail)
logfile = codecs.open(logfilename, "w", "utf-8")
logfile.write(inmail)
logfile.close()

### Load p≡p ######################################################################################

import pEp
pEp.set_debug_log_enabled(True) # TODO
pEp.message_to_send = messageToSend
pEp.notify_handshake = notifyHandshake

dbg("p≡p (" + str(pEp.about).strip().replace("\n", ", ") + ", p≡p engine version " + pEp.engine_version + ") loaded in", True)

### Import static / global keys ###################################################################

if initialimport:
	dbg(c("Initializing keys.db...", 2))

	for f in glob(statickpath + ouraddr + "*.asc"):
		dbg("")
		keys = open(f, "rb").read()
		pEp.import_key(keys)
		dbg("Imported static/predefined keys from " + f, True)

	for f in glob(globalkpath + "*.asc"):
		dbg("")
		keys = open(f, "rb").read()
		pEp.import_key(keys)
		dbg("Imported global key(s) from " + f, True)

	# for f in glob(exportedpath + ouraddr + "/sec.*.asc"):
		# dbg("Importing GnuPG-exported secret key from file: " + f)
		# keys = open(f, "rb").read()
		# pEp.import_key(keys)

	# for f in glob(exportedpath + ouraddr + "/pub.*.asc"):
		# dbg("Importing GnuPG-exported public key from file: " + f)
		# keys = open(f, "rb").read()
		# pEp.import_key(keys)

### Show me what you got ##########################################################################

dbg(c("┌ Environment variables", 5) + "\n" + prettytable(os.environ))
# dbg(c("┌ Keys in this keyring (as stored in keys.db)", 5) + "\n" + prettytable(keysfromkeyring()))
dbg(c("┌ Headers in original message", 5) + "\n" + prettytable(getmailheaders(inmail)))

### Check if we have a public key for "them" ######################################################

if mode == "encrypt":
	theirkey = keysfromkeyring(theiraddr)
	if theirkey == False:
		dbg("No public key for recipient " + c(theiraddr, 3) + ", p≡p won't be able to encrypt this time")
		theirpepid = pEp.Identity(theiraddr, theiraddr)
	else:
		dbg(c("Found existing public key for recipient ", 2) + c(theiraddr, 5) + ":\n" + prettytable(theirkey))
		# TODO: this doesn't really support multiple UID's per key, should probably figure out the most recent
		theirkeyname = theirkey[0]['key_blob']['username']
		theirkeyaddr = theirkey[0]['pEp_keys.db']['UserID']
		theirkeyfp   = theirkey[0]['pEp_keys.db']['KeyID']
		dbg("Their key name: " + theirkeyname)
		dbg("Their key addr: " + theirkeyaddr)
		dbg("Their key fpr:  " + theirkeyfp)

		theirpepid = pEp.Identity(theirkeyaddr, theirkeyname)

### Check if we have a private key for "us" #######################################################

ourkey = keysfromkeyring(ouraddr)
if ourkey == False:
	dbg("No private key for our address " + c(ouraddr, 3) + ", p≡p will have to generate one later")
else:
	dbg(c("Found existing private key for our address ", 2) + c(ouraddr, 5) + ":\n" + prettytable(ourkey))
	# TODO: this doesn't really support multiple UID's per key, should probably figure out the most recent
	ourkeyname = ourkey[0]['key_blob']['username']
	ourkeyaddr = ourkey[0]['pEp_keys.db']['UserID']
	ourkeyfp   = ourkey[0]['pEp_keys.db']['KeyID']
	dbg("  Our key name: " + ourkeyname)
	dbg("  Our key addr: " + ourkeyaddr)
	dbg("  Our key fpr:  " + ourkeyfp)

### Create/set own identity ######################################################################

ourname = jsonlookup(usermappath, ouraddr, False)

try:
	ourkeyname, ourkeyaddr, ourkeyfp
except NameError:
	dbg(c("No existing key found, letting p≡p generate one", 3))
	if ourname is None:
		import re
		ourname = re.sub(r"\@", " at ", ouraddr)
		ourname = re.sub(r"\.", " dot ", ourname)
		ourname = re.sub(r"\W+", " ", ourname)
		dbg(c("No matching name found", 1) + " for address " + c(ouraddr, 3) + ", using de-@'ed address as name: " + c(ourname, 5))
	else:
		dbg("Found name matching our address " + c(ouraddr, 3) + ": " + c(ourname, 2))

	i = pEp.Identity(ouraddr, ourname)
	pEp.myself(i)
	ourpepid = pEp.Identity(ouraddr, ourname) # redundancy needed since we can't use myself'ed or update'd keys in pEp.Message.[to|from]
else:
	dbg(c("Found existing key, p≡p will import/use it", 2))
	if ourname is not None and ourname != ourkeyname:
		dbg(c("Name inside existing key (" + ourkeyname + ") differs from the one found in username.map (" + ourname + "), using the latter", 3))
		i = pEp.Identity(ourkeyaddr, ourname)
		ourpepid = pEp.Identity(ourkeyaddr, ourname) # redundancy needed since we can't use myself'ed or update'd keys in pEp.Message.[to|from]
	else:
		i = pEp.Identity(ourkeyaddr, ourkeyname)
		ourpepid = pEp.Identity(ourkeyaddr, ourkeyname) # redundancy needed since we can't use myself'ed or update'd keys in pEp.Message.[to|from]

	i.fpr = ourkeyfp
	# i.update() # Not really needed it seems but keep for future reference

### Prepare message for processing by p≡p #########################################################

try:
	src = pEp.Message(inmail)

	if mode == "encrypt":
		src.sent = int(str(datetime.now().timestamp()).split('.')[0])
		src.id = "pEp-" + uuid4().hex + "@" + socket.getfqdn()
		src.from_ = ourpepid
		src.to = [theirpepid]
		reply_to = jsonlookup(fwdmappath, ourpepid.address, False)
		if reply_to is not None:
			dbg(c("Overriding Reply-To: " + ourpepid.username + " <" + reply_to + ">", 3) + " (From: " + ourpepid.address + ")")
			reply_to_i = pEp.Identity(reply_to, ourpepid.username)
			src.from_ = reply_to_i
			# src.reply_to = [ reply_to_i ] # TODO: this would be cleaner but pEp on the other end doesn't handle this yet


	if mode == "decrypt":
		src.to = [ourpepid]
		src.recv_by = ourpepid # TODO: implement proper echo-protocol handling
		### src.reply_to = [theirpepid]

	# Get rid of CC and BCC for loop-avoidance (since Postfix gives us one separate message per recipient)
	src.cc = []
	src.bcc = []

except Exception:
	e = sys.exc_info()
	errmsg  = "ERROR 1 - " + str(e[0]) + ": " + str(e[1]) + "\n"
	errmsg += "Traceback:\n" + prettytable([line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])])
	dbg(errmsg)
	dbgmail(errmsg)
	exit(1)
	# pass

try:
	dbg("Processing message from " + ((c(src.from_.username, 2)) if len(src.from_.username) > 0 else "") + c(" <" + src.from_.address + ">", 3) + \
							" to " + ((c(src.to[0].username, 2)) if len(src.to[0].username) > 0 else "") + c(" <" + src.to[0].address + ">", 3))
except Exception:
	e = sys.exc_info()
	errmsg  = "Couldn't get src.from_ or src.to\n"
	errmsg += "ERROR 2 - " + str(e[0]) + ": " + str(e[1]) + "\n"
	errmsg += "Traceback:\n" + prettytable([line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])])
	dbg(errmsg)
	dbgmail(errmsg)
	exit(2)
	# pass

# Workaround for message_api.c:632: separate_short_and_long: Assertion `src' failed
try:
	if len(src.longmsg) == 0:
		if len(src.longmsg_formatted) > 0:
			dbg("Fixed missing text-only part in multipart/alternate message")
			src.longmsg = src.longmsg_formatted
		else:
			dbg("Fallback-fixed missing text-only part in multipart/alternate message")
			src.longmsg = "(content missing)"
except Exception:
	e = sys.exc_info()
	errmsg  = "ERROR 3 - " + str(e[0]) + ": " + str(e[1]) + "\n"
	errmsg += "Traceback:\n" + prettytable([line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])])
	dbg(errmsg)
	dbgmail(errmsg)
	exit(3)
	# pass

### Log parsed message ############################################################################

logfilename = os.path.join(logpath, "in." + mode + ".parsed.eml")
dbg("p≡p-parsed message: " + c(logfilename, 6))
# dbg(str(src)[0:3615])
logfile = codecs.open(logfilename, "w", "utf-8")
logfile.write(str(src))
logfile.close()

### Let p≡p do it's magic #########################################################################

try:
	if mode == "encrypt":
		# Silly workaround for senders that don't bother to include a username
		if len(src.from_.username) == 0:
			tmp = pEp.Identity(src.from_.address, src.from_.address)
			src.from_ = tmp
			dbg("Added missing username to src._from: " + repr(src.from_))

		# Blacklisted domains which don't like PGP
		a = src.to[0].address
		d = a[a.find("@") + 1:]
		if d in bldomains:
			dbg(c("Blacklisted domain " + d + ". Not encrypting", 5))
			dst = src
		# Magic-string "NOENCRYPT" found inside the message
		elif "NOENCRYPT" in src.longmsg + src.longmsg_formatted:
			dbg(c("Found magic string 'NOENCRYPT' so not going to encrypt this message", 1))
			dst = src
			dst.longmsg = dst.longmsg.replace("NOENCRYPT", "")
			dst.longmsg_formatted = dst.longmsg_formatted.replace("NOENCRYPT", "")
		elif src.from_.address == src.to[0].address:
			dbg(c("Sender == recipient so probably a loopback/test-message, skipping encryption...", 1))
			dst = src
		else:
			dbg(c("Encrypting message...", 2))

			if theirkey == False:
				dbg("We DO NOT have a key for this recipient")
			else:
				dbg("We have a key for this recipient:\n" + prettytable(theirkey))

			# pEp.unencrypted_subject(True)

			# dst = src.encrypt()
			dst = src.encrypt(["4BBCDBF5967AA2BDB26B5877C3329372697276DE"], 0) # TODO: load extra keys from some config/map
			# dst = src # DEBUG: disable encryption

			dbg(c("Processed in", 2), True)

			# DEBUG
			dbg("Full dst:\n" + str(dst))
			inspectusingsq(str(dst))

	if mode == "decrypt":
		pepfails = False # Set to True if Postfix queue fills up with errors
		if not pepfails:
			dbg(c("Decrypting message via pEp...", 2))
			dst, keys, rating, flags = src.decrypt()
			dst.to = [ourpepid] # Lower the (potentially rewritten) outer recipient back into the inner message
		else:
			dbg(c("Decrypting message via Sequoia...", 2))
			keys, rating, flags = None, None, None

			tmp = pEp.Message(decryptusingsq(inmail, os.path.join(workdirpath, "sec." + ouraddr + ".*.key")))

			# dbg("TMP s: " + tmp.shortmsg)
			# dbg("TMP l: " + tmp.longmsg)
			dst = src
			dst.shortmsg = tmp.shortmsg
			dst.longmsg = tmp.longmsg
			dst.attachments = []

			# Fallback of the fallback: just forward the encrypted message as-is
			# dst, keys, rating, flags = src, None, None, None

			# dbg("TMP: "  + c(str(tmp), 1))
			dbg("DST: " + c(str(dst), 2))
			# dbg("DSTs: " + c(str(dst.shortmsg), 3))
			# dbg("DSTl: " + c(str(dst.longmsg), 4))
	
			keys = [ "Decrypted_by_Sequoia-info_not_available" ] # must stay for "if keys is None" below
	
		# if pepfails:
			# dbg(c("pEp wasn't able to decrypt -.-", 1))
			# exit(2)

		if keys is None or len(keys) == 0:
			dbg("Original message was NOT encrypted")
		else:
			dbg("Original message was encrypted to these keys:\n" + prettytable(list(set(keys))))

		dbg(c("Decrypted in", 2), True)

	# Workaround for engine converting plaintext-only messages into a msg.txt inline-attachment
	# dst = str(dst).replace(' filename="msg.txt"', "")

except Exception:
	e = sys.exc_info()
	errmsg  = "ERROR 4 - " + str(e[0]) + ": " + str(e[1]) + "\n"
	errmsg += "Traceback:\n" + prettytable([line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])])
	dbg(errmsg)
	dbgmail(errmsg)
	exit(4)
	# dst = src # FALLBACK: forward original message as-is if anything crypto goes wrong
	# pass

### Add MX routing and version information headers ################################################

dbg("Opt fields IN:\n" + prettytable(dst.opt_fields)) # DEBUG

opts = {
	"X-pEpGate-mode": mode,
	"X-pEpGate-version": gateversion,
	"X-pEpEngine-version": pEp.engine_version,
	"X-NextMX": "auto",
}

if mode == "encrypt":
	nextmx = jsonlookup(nextmxpath, theirpepid.address[theirpepid.address.rfind("@") + 1:], False)

if mode == "decrypt":
	nextmx = jsonlookup(nextmxpath, ourpepid.address[ourpepid.address.rfind("@") + 1:], False)

if nextmx is not None:
	dbg(c("Overriding next MX: " + nextmx, 3))
	opts['X-NextMX'] = nextmx

opts.update(dst.opt_fields)
dst.opt_fields = opts

dbg("Opt fields OUT:\n" + prettytable(dst.opt_fields)) # DEBUG

### Log processed message #########################################################################

dst = str(dst)

logfilename = os.path.join(logpath, "in." + mode + ".processed.eml")
dbg("p≡p-processed message: " + c(logfilename, 6) + "\n" + str(dst)[0:1337])
logfile = codecs.open(logfilename, "w", "utf-8")
logfile.write(dst)
logfile.close()

### Hand reply over to sendmail ###################################################################

dbg("Sending mail via MX: " + (c("auto", 3) if nextmx is None else c(str(nextmx), 1)))
dbg("From: " + ((c(src.from_.username, 2)) if len(src.from_.username) > 0 else "") + c(" <" + src.from_.address + ">", 3))
dbg("  To: " + ((c(src.to[0].username, 2)) if len(src.to[0].username) > 0 else "") + c(" <" + src.to[0].address + ">", 3))

# if mode == "decrypt":
	# TODO: add header with info about all keys to which the original msg was encrytped to
	# TODO: if "PEPFEEDBACK" in msg body also return the above as separate mail to sender

# if mode == "encrypt":
	# TODO: add header with info about which keys the msg has been encrypted to (incl. extra keys)

# sendmail("X-NextMX: 192.168.10.10:25\n" + inmail)
# sendmail(inmail)

sendmail(dst)

dbg("===== " + c("p≡pgate ended", 1) + " =====")
