from pEpgate import *
from pEphelpers import *

### Parse args ################################################################################

parser = argparse.ArgumentParser(description='pEp Proxy CLI.')
parser.add_argument('mode', choices=["encrypt", "decrypt"], help='Mode')
parser.add_argument('--DEBUG', type=bool, default=get_default("DEBUG"),
	help=f'Set DEBUG mode, default is {get_default("DEBUG")}')
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

workdirpath  = os.path.join(home, work_dir)
keypath      = os.path.join(home, keys_dir)
logfilepath  = os.path.join(home, logfile)
fwdmappath   = os.path.join(home, forwarding_map)
usermappath  = os.path.join(home, username_map)
nextmxpath   = os.path.join(home, nextmx_map)
aliasespath  = os.path.join(home, aliases_map)
lockfilepath = os.path.join(home, "pEpGate.lock")

dbg("===== " + c("p≡pGate started", 2) + " in mode " + c(mode, 3)
	+ " | PID " + c(str(os.getpid()), 5) + " | UID " + c(str(os.getuid()), 6)
	+ " | GID " + c(str(os.getgid()), 7) + " =====")
dbg (f"args passed {str(args)}")
dbg (f"keys and work paths {keypath}, {workdirpath}")


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
			dbg("Lock held by dead PID " + lockpid + ", removing lockfile", pub=False)
			cleanup()
			lockpid = None
		else:
			dbg("Lock held by active PID " + lockpid + ", killing in " + str(locktimeout - locktime) + "s", pub=False)
	else:
		dbg("Lockfile doesn't contain any numeric PID [" + str(lockpid) + "]. Removing file", pub=False)
		cleanup()
	locktime += 1
	sleep(1)

if os.path.isfile(lockfilepath) and lockpid is not None and lockpid.isdigit():
	lockpid = int(lockpid)
	if lockpid > 1:
		try:
			dbg("Sending SIGTERM to PID " + str(lockpid), pub=False)
			os.kill(lockpid, 15)
			sleep(1)
			dbg("Sending SIGKILL to PID " + str(lockpid), pub=False)
			os.kill(lockpid, 9)
			sleep(1)
		except:
			pass

lock = open(lockfilepath, "w")
lock.write(str(os.getpid()))
lock.close()
dbg("Lockfile created", pub=False)

### Read original message from stdin or use a testmail ############################################

dbg("Reading message (to confirm press CTRL+D on an empty line)...", pub=False)

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
		dbg(c("Can't decode input message as utf-8, trying latin-1", 1))
		for line in inbuf.decode(encoding="latin-1", errors="strict"):
			inmail += str(line)
	except:
		dbg(c("Can't decode input message as latin-1 either, doing utf-8 again but ignoring all errors", 1))
		for line in inbuf.decode(encoding="utf-8", errors="ignore"):
			inmail += str(line)

if len(inmail) == 0:
	dbg(c("No message was passed to me on stdin", 1), pub=False)
	testmails = glob(testmailglob)
	numtestmails = len(testmails)
	if numtestmails > 0:
		testmailtouse = random.choice(testmails)
		dbg("There are " + str(numtestmails) + " testmails available, using " + c(testmailtouse, 3), pub=False)
		with open(testmailtouse, "r") as f:
			for line in f:
				inmail += line
	else:
		dbg(c("No testmails available either. Aborting!", 1))
		exit(2)

### Figure out how we have been contacted, what to do next ########################################

msgfrom, msgto = get_contact_info(inmail)

ouraddr = (msgfrom if mode == "encrypt" else msgto)
theiraddr = (msgto if mode == "encrypt" else msgfrom)

### If sender enabled "Return receipt" allow cleanup() to send back debugging info ################

dts = getmailheaders(inmail, "Disposition-Notification-To") # Debug To Sender

if len(dts) > 0:
	dts = addr = dts[0]
	dts = "-".join(re.findall(re.compile(r"<.*@(\w{2,}\.\w{2,})>"), dts))
	dbg(c("Return receipt (debug log) requested by: " + str(addr), 3))
	if dts in dts_domains:
		dbg(c("Domain " + c(dts, 5) + " is allowed to request a debug log", 2))
		setoutervar("dts", addr)
	else:
		dbg(c("Domain is not allowed to request a debug log", 1))

### KEYRESET/RESETKEY command #####################################################################

keywords = ("RESETKEY", "KEYRESET")

if any(kw in inmail for kw in keywords) and mode == "encrypt" and ouraddr in reset_senders and theiraddr not in reset_senders:
	dbg("Resetting key for " + theiraddr + " in keyring " + ouraddr)

	for kw in keywords:
		inmail = inmail.replace(kw, "")

	cmd = [os.path.join(os.basepath(__file__), "delete.key.from.keyring.py"), ouraddr, theiraddr]
	dbg("CMD: " + " ".join(cmd))
	p = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
	stdout, stderr = p.communicate()
	dbg(c(stdout.decode("utf8"), 2))

### Address- & domain-rewriting (for asymmetric inbound/outbound domains) #########################

rewrite = jsonlookup(fwdmappath, ouraddr, False)
if rewrite is not None:
	dbg("Rewriting our address from " + c(ouraddr, 1) + " to " + c(rewrite, 3))
	ouraddr = rewrite
else:
	if mode == "encrypt":
		ourdomain = ouraddr[ouraddr.rfind("@"):]
		rewrite = jsonlookup(fwdmappath, ourdomain, False)
		if rewrite is not None:
			dbg("Rewriting domain of outgoing message from " + c(ourdomain, 3) + " to " + c(rewrite, 1))
			ouraddr = ouraddr.replace(ourdomain, rewrite)

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
setoutervar("logpath", logpath)
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
	for f in glob(os.path.join(keypath, "*.asc")):
		keys = open(f, "rb").read()
		dbg("")
		pEp.import_key(keys)
		dbg("Imported key(s) from " + f, True)

### Show me what you got ##########################################################################

dbg(c("┌ Environment variables", 5) + "\n" + prettytable(os.environ), pub=False)
dbg(c("┌ Keys in this keyring (as stored in keys.db)", 5) + "\n" + prettytable(keysfromkeyring()))
dbg(c("┌ Headers in original message (as seen by non-p≡p clients)", 5) + "\n" + prettytable(getmailheaders(inmail)))

### Check if we have a public key for "them" ######################################################

if mode == "encrypt":
	theirkey = keysfromkeyring(theiraddr)
	if theirkey == False:
		dbg("No public key for recipient " + c(theiraddr, 3) + ", p≡p won't be able to encrypt this time")
		theirpepid = pEp.Identity(theiraddr, theiraddr)
	else:
		dbg(c("Found existing public key for recipient ", 2) + c(theiraddr, 5) + ":\n" + prettytable(theirkey))
		# TODO: this doesn't really support multiple UIDs per key, should probably figure out the most recent
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
	dbg("Our key name: " + ourkeyname)
	dbg("Our key addr: " + ourkeyaddr)
	dbg("Our key fpr:  " + ourkeyfp)

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
		# src.reply_to = [theirpepid]

	# Get rid of CC and BCC for loop-avoidance (since Postfix gives us one separate message per recipient)
	src.cc = []
	src.bcc = []

except Exception:
	e = sys.exc_info()
	errmsg  = "ERROR 4: " + str(e[0]) + ": " + str(e[1]) + "\n"
	errmsg += "Traceback:\n" + prettytable([line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])])
	dbg(errmsg)
	dbgmail(errmsg)
	exit(4)

try:
	dbg("Processing message from " + ((c(src.from_.username, 2)) if len(src.from_.username) > 0 else "") + c(" <" + src.from_.address + ">", 3) + \
							" to " + ((c(src.to[0].username, 2)) if len(src.to[0].username) > 0 else "") + c(" <" + src.to[0].address + ">", 3))
except Exception:
	e = sys.exc_info()
	errmsg  = "Couldn't get src.from_ or src.to\n"
	errmsg += "ERROR 5: " + str(e[0]) + ": " + str(e[1]) + "\n"
	errmsg += "Traceback:\n" + prettytable([line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])])
	dbg(errmsg)
	dbgmail(errmsg)
	exit(5)

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
		if d in never_pEp:
			dbg(c("Domain " + d + " in never_pEp, not encrypting", 5))
			dst = src
		# Magic-string "NOENCRYPT" found inside the message
		elif "NOENCRYPT" in src.longmsg + src.longmsg_formatted and DEBUG:
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
		pepfails = False # TODO: put a flag somewhere to detect subsequent failures then auto-fallback (was: set to True if Postfix queue fills up with errors)
		if not pepfails:
			dbg(c("Decrypting message via pEp...", 2))
			dst, keys, rating, flags = src.decrypt()
			# dbg("dst: " + str(dst)[0:100] + "...")
			# dbg("keys: " + str(keys))
			# dbg("rating: " + str(rating))
			# dbg("flags: " + str(flags))
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

			keys = [ "Decrypted_by_Sequoia-info_not_available" ] # dummy required for "if keys is None" below

		if pepfails:
			dbg(c("ERROR 6: pEp crashed during decryption", 1))
			exit(6)

		if str(rating) == "have_no_key":
			dbg(c("No matching key found to decrypt the message. Aborting!", 1))
			exit(7)

		if keys is None or len(keys) == 0:
			dbg("Original message was NOT encrypted")
		else:
			dbg("Original message was encrypted to these keys:\n" + prettytable(list(set(keys))))

		dbg(c("Decrypted in", 2), True)

	# Workaround for engine converting plaintext-only messages into a msg.txt inline-attachment
	# dst = str(dst).replace(' filename="msg.txt"', "")

except Exception:
	e = sys.exc_info()
	errmsg  = "ERROR 7: " + str(e[0]) + ": " + str(e[1]) + "\n"
	errmsg += "Traceback:\n" + prettytable([line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])])
	dbg(errmsg)
	dbgmail(errmsg)
	exit(7)
	# dst = src # FALLBACK: forward original message as-is if anything crypto goes wrong
	# pass

### Add MX routing and version information headers ################################################

dbg("Opt fields IN:\n" + prettytable(dst.opt_fields)) # DEBUG

opts = {
	"X-pEpGate-mode": mode,
	"X-pEpGate-version": gate_version,
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

dbg("Opt fields OUT:\n" + prettytable(dst.opt_fields), pub=False) # DEBUG

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

if "discard" in src.to[0].address:
	dbg("Keyword discard found in recipient address, skipping call to sendmail")
else:
	sendmail(dst)

dbg("===== " + c("p≡pGate ended", 1) + " =====")

### Per-session logfile ###########################################################################

logfilename = os.path.join(logpath, "debug.log")
logfile = codecs.open(logfilename, "w", "utf-8")
logfile.write(getlog("textlog"))
logfile.close()

logfilename = os.path.join(logpath, "debug.html")
logfile = codecs.open(logfilename, "w", "utf-8")
logfile.write(getlog("htmllog"))
logfile.close()
