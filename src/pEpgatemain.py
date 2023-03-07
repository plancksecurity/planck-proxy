import os
import sys
import re
import codecs
import importlib

from uuid        import uuid4
from time        import sleep
from datetime    import datetime
from glob        import glob
from pathlib 	 import Path
from subprocess  import Popen, PIPE, STDOUT

from pEpgatesettings import settings
from pEphelpers import *
from scripts import deletekeyfromkeyring


def print_init_info(args):
	dbg("===== " + c("p≡pGate started", 2) + " in mode " + c(settings['mode'], 3)
		+ " | PID " + c(str(os.getpid()), 5) + " | UID " + c(str(os.getuid()), 6)
		+ " | GID " + c(str(os.getgid()), 7) + " =====")
	if settings['DEBUG']:
		dbg (c("┌ Parameters", 5) + "\n" + prettytable(args.__dict__))
		cur_settings = settings.copy()
		for setting in ['adminlog', 'textlog', 'htmllog']:
			cur_settings.pop(setting)
		dbg (c("┌ Settings (except logs)", 5) + "\n" + prettytable(cur_settings))


def init_lockfile():
	"""
	Lockfile handling
	"""

	locktime = 0
	lockpid = None

	while os.path.isfile(settings['lockfilepath']) and locktime < settings['locktimeout'] :
		lock = open(settings['lockfilepath'], "r")
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
				dbg("Lock held by active PID " + lockpid + ", killing in " + str(settings['locktimeout']  - locktime) + "s", pub=False)
		else:
			dbg("Lockfile doesn't contain any numeric PID [" + str(lockpid) + "]. Removing file", pub=False)
			cleanup()
		locktime += 1
		sleep(1)

	if os.path.isfile(settings['lockfilepath']) and lockpid is not None and lockpid.isdigit():
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

	lock = open(settings['lockfilepath'], "w")
	lock.write(str(os.getpid()))
	lock.close()
	dbg("Lockfile created", pub=False)


def get_message(msg):
	"""
	Read original message from stdin or use a testmail
	"""

	dbg("Reading message (to confirm press CTRL+D on an empty line)...", pub=False)

	inbuf = bytearray()
	inmail = ""
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
		dbg(c("No message was passed to me. Aborting.", 1), pub=False)
		exit(2)

	msg['inmail'] = inmail
	return msg

def set_addresses(msg, us, them):
	"""
	Figure out how we have been contacted, what to do next
	"""
	msgfrom, msgto = get_contact_info(msg['inmail'])

	ouraddr = (msgfrom if settings['mode'] == "encrypt" else msgto)
	theiraddr = (msgto if settings['mode'] == "encrypt" else msgfrom)
	msg['msgfrom'] = msgfrom
	msg['msgto'] = msgto

	us['addr'] = ouraddr
	them['addr'] = theiraddr

	return msg, us, them


def enable_dts( msg):
	"""
	If sender enabled "Return receipt" allow cleanup() to send back debugging info
	"""
	global settings
	dts = getmailheaders(msg['inmail'], "Disposition-Notification-To") # Debug To Sender

	if len(dts) > 0:
		addr = dts[0]
		dts = "-".join(re.findall(re.compile(r"<?.*@(\w{2,}\.\w{2,})>?"), addr))
		dbg(c("Return receipt (debug log) requested by: " + str(addr), 3))
		if dts in settings['dts_domains']:
			dbg(c("Domain " + c(dts, 5) + " is allowed to request a debug log", 2))
			settings["dts"] = addr
		else:
			dbg(c("Domain is not allowed to request a debug log", 1))

def check_key_reset(msg, us, them):
	"""
	If 'RESETKEY' or 'KEYRESET' are found in a mail in mode encrypt, delete theiraddr from ouraddr keyring.
	"""

	keywords = ("RESETKEY", "KEYRESET")

	if (kw in msg['inmail'] for kw in keywords) and settings['mode'] == "encrypt" and us['addr'] in settings['reset_senders'] and them['addr'] not in settings['reset_senders']:
		dbg("Resetting key for " + them['addr'] + " in keyring " + us['addr'])

		for kw in keywords:
			msg['inmail'] = msg['inmail'].replace(kw, "")

		keys_db_location = os.path.join(str(settings['workdir']), '.pEp')
		deletekeyfromkeyring.delete_key(us['addr'], them['addr'], keys_db_location)

	return msg

# ### Address- & domain-rewriting (for asymmetric inbound/outbound domains) #########################

def addr_domain_rewrite(us):
	"""
	Address- & domain-rewriting (for asymmetric inbound/outbound domains)
	"""

	forwarding_map_path = os.path.join(settings['home'] , settings['forwarding_map'])
	rewrite = jsonlookup(forwarding_map_path, us['addr'], False)
	if rewrite is not None:
		dbg("Rewriting our address from " + c(us['addr'], 1) + " to " + c(rewrite, 3))
		us['addr'] = rewrite
	else:
		ourdomain = us['addr'][us['addr'].rfind("@"):]
		rewrite = jsonlookup(forwarding_map_path, ourdomain, False)
		if rewrite is not None:
			dbg("Rewriting domain of message from " + c(ourdomain, 3) + " to " + c(rewrite, 1))
			us['addr'] = us['addr'].replace(ourdomain, rewrite)
	return us

# ### Create & set working directory ################################################################

def init_workdir(us):
	"""
	Create workdir for ouraddr, and set it to the current $HOME
	"""
	global settings
	workdirpath = os.path.join(settings['home'] , settings['work_dir'], us['addr'])
	if not os.path.exists(workdirpath):
		os.makedirs(workdirpath)

	os.environ['HOME'] = workdirpath
	os.chdir(workdirpath)

	settings['work_dir'] = workdirpath
	if settings['DEBUG']:
		dbg(f"init workdir to {settings['work_dir']}")

### Check if Sequoia-DB already exists, if not import keys later using p≡p ########################

def check_initial_import():
	keys_db_path = os.path.join(os.environ["HOME"], '.pEp', 'keys.db')
	return not os.path.exists(keys_db_path)

# ### Summary #######################################################################################

def print_summary_info(msg, us, them):
	dbg("       Message from: " + c(str(msg['msgfrom']), 5))
	dbg("         Message to: " + c(str(msg['msgto']), 5))
	dbg("        Our address: " + c(us['addr'], 3))
	dbg("      Their address: " + c(them['addr'], 3))
	dbg("    Initital import: " + ("Yes" if check_initial_import() else "No"))

# ### Logging #######################################################################################

def init_logging(msg, them):
	"""
	Log original message into the workdir
	"""
	global settings
	logpath = os.path.join(settings['work_dir'], them['addr'], datetime.now().strftime('%Y.%m.%d-%H.%M.%S.%f'))
	settings['logpath'] = logpath
	if not os.path.exists(logpath):
		os.makedirs(logpath)

	logfilename = os.path.join(logpath, "in." + settings['mode'] + ".original.eml")
	dbg("   Original message: " + c(logfilename, 6)) # + "\n" + inmail)
	logfile = codecs.open(logfilename, "w", "utf-8")
	logfile.write(msg['inmail'])
	logfile.close()

	if settings['DEBUG']:
		dbg(f"init logpath to {settings['logpath']}")

# ### Load p≡p ######################################################################################

def load_pep():
	"""
	Import the p≡p engine. This will create the .pEp folder in the current $HOME
	This method should never be called before init_workdir
	"""
	pEp = importlib.import_module('pEp')
	pEp.set_debug_log_enabled(True) # TODO
	pEp.message_to_send = messageToSend
	pEp.notify_handshake = notifyHandshake

	dbg("p≡p (" + str(pEp.about).strip().replace("\n", ", ") + ", p≡p engine version " + pEp.engine_version + ") loaded in", True)
	return pEp

# ### Import static / globally available / extra keys ###############################################

def import_keys(pEp):
	"""
	Import keys from the keys_dir
	"""
	dbg(c("Initializing keys.db...", 2))
	keys_path = os.path.join(settings['home'] , settings['keys_dir'])
	key_files = glob(os.path.join(keys_path, "*.asc"))
	for f in key_files:
		keys = open(f, "rb").read()
		dbg("")
		pEp.import_key(keys)
		dbg("Imported key(s) from " + f, True)

# ### Show me what you got ##########################################################################
def print_keys_and_keaders(msg):
	dbg(c("┌ Environment variables", 5) + "\n" + prettytable(os.environ), pub=False)
	dbg(c("┌ Keys in this keyring (as stored in keys.db)", 5) + "\n" + prettytable(keysfromkeyring()))
	dbg(c("┌ Headers in original message (as seen by non-p≡p clients)", 5) + "\n" + prettytable(getmailheaders(msg['inmail'])))

# ### Check if we have a public key for "them" ######################################################

def check_recipient_pubkey(pEp, them):
	"""
	Check if we have a key to encrypt for the recipient and get their p≡p identity
	"""
	theirkey = keysfromkeyring(them['addr'])
	them['key'] = theirkey
	if theirkey == False:
		dbg("No public key for recipient " + c(them['addr'], 3) + ", p≡p won't be able to encrypt this time")
		theirpepid = pEp.Identity(them['addr'], them['addr'])
	else:
		dbg(c("Found existing public key for recipient ", 2) + c(them['addr'], 5) + ":\n" + prettytable(theirkey))
		# TODO: this doesn't support multiple UID's per key, we should figure out the most recent one
		theirkeyname = theirkey[0]['key_blob']['username']
		theirkeyaddr = theirkey[0]['pEp_keys.db']['UserID']
		theirkeyfpr   = theirkey[0]['pEp_keys.db']['KeyID']
		dbg("Their key name: " + theirkeyname)
		dbg("Their key addr: " + theirkeyaddr)
		dbg("Their key fpr:  " + theirkeyfpr)
		them['keyname'] = theirkeyname
		them['keyaddr'] = theirkeyaddr
		them['keyfpr'] = theirkeyfpr

		theirpepid = pEp.Identity(theirkeyaddr, theirkeyname)

	them['pepid'] = theirpepid

	return them

# ### Check if we have a private key for "us" #######################################################

def check_sender_privkey(us):
	"""
	Check if we have a public key for the sender
	"""
	ourkey = keysfromkeyring(us['addr'])
	if ourkey == False:
		dbg("No private key for our address " + c(us['addr'], 3) + ", p≡p will have to generate one later")
		ourkeyname = ourkeyaddr = ourkeyfpr = None
	else:
		dbg(c("Found existing private key for our address ", 2) + c(us['addr'], 5) + ":\n" + prettytable(ourkey))
		# TODO: this doesn't support multiple UID's per key, we should figure out the most recent one
		ourkeyname = ourkey[0]['key_blob']['username']
		ourkeyaddr = ourkey[0]['pEp_keys.db']['UserID']
		ourkeyfpr   = ourkey[0]['pEp_keys.db']['KeyID']
		dbg("Our key name: " + ourkeyname)
		dbg("Our key addr: " + ourkeyaddr)
		dbg("Our key fpr:  " + ourkeyfpr)

		us['keyname'] = ourkeyname
		us['keyaddr'] = ourkeyaddr
		us['keyfpr'] = ourkeyfpr

	return us

# ### Create/set own identity ######################################################################
def set_own_identity(pEp, us):
	"""
	Create or set our own p≡p identity
	"""
	username_map_path = os.path.join(settings['home'] , settings['username_map'])
	ourname = jsonlookup(username_map_path, us['addr'], False)

	try:
		us['keyname'], us['keyaddr'], us['keyfpr']
	except KeyError:
		dbg(c("No existing key found, letting p≡p generate one", 3))
		if ourname is None:
			import re
			ourname = re.sub(r"\@", " at ", us['addr'])
			ourname = re.sub(r"\.", " dot ", ourname)
			ourname = re.sub(r"\W+", " ", ourname)
			dbg(c("No matching name found", 1) + " for address " + c(us['addr'], 3) + ", using de-@'ed address as name: " + c(ourname, 5))
		else:
			dbg("Found name matching our address " + c(us['addr'], 3) + ": " + c(ourname, 2))

		i = pEp.Identity(us['addr'], ourname)
		pEp.myself(i)
		ourpepid = pEp.Identity(us['addr'], ourname) # redundancy needed since we can't use myself'ed or update'd keys in pEp.Message.[to|from]
	else:
		dbg(c("Found existing key, p≡p will import/use it", 2))
		if ourname is not None and ourname != us['keyname']:
			dbg(c("Name inside existing key (" + us['keyname'] + ") differs from the one found in username.map (" + ourname + "), using the latter", 3))
			i = pEp.Identity(us['keyaddr'], ourname)
			ourpepid = pEp.Identity(us['keyaddr'], ourname) # redundancy needed since we can't use myself'ed or update'd keys in pEp.Message.[to|from]
		else:
			i = pEp.Identity(us['keyaddr'], us['keyname'])
			ourpepid = pEp.Identity(us['keyaddr'], us['keyname']) # redundancy needed since we can't use myself'ed or update'd keys in pEp.Message.[to|from]

		i.fpr = us['keyfpr']

	us['pepid'] = ourpepid

	return us

# ### Prepare message for processing by p≡p #########################################################

def create_pEp_message(pEp, msg, us, them):
	"""
	Create a p≡p message object
	"""
	try:
		src = pEp.Message(msg['inmail'])

		if settings['mode'] == "encrypt":
			src.sent = int(str(datetime.now().timestamp()).split('.')[0])
			src.id = "pEp-" + uuid4().hex + "@" + socket.getfqdn()
			src.from_ = us['pepid']
			src.to = [them['pepid']]

		if settings['mode'] == "decrypt":
			src.to = [us['pepid']]
			src.recv_by = us['pepid'] # TODO: implement proper echo-protocol handling

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

	# Log parsed message

	logfilename = os.path.join(settings['logpath'], "in." + settings['mode'] + ".parsed.eml")
	dbg("p≡p-parsed message: " + c(logfilename, 6))
	logfile = codecs.open(logfilename, "w", "utf-8")
	logfile.write(str(src))
	logfile.close()

	msg['src'] = src

	return msg


# ### Let p≡p do it's magic #########################################################################
def process_message(pEp, msg, us, them):
	try:
		if settings['mode'] == "encrypt":
			# Silly workaround for senders that don't bother to include a username
			if len(msg['src'].from_.username) == 0:
				tmp = pEp.Identity(msg['src'].from_.address, msg['src'].from_.address)
				msg['src'].from_ = tmp
				dbg("Added missing username to src._from: " + repr(msg['src'].from_))

			# Blacklisted domains which don't like PGP
			a = msg['src'].to[0].address
			d = a[a.find("@") + 1:]
			if d in settings['never_pEp']:
				dbg(c("Domain " + d + " in never_pEp, not encrypting", 5))
				dst = msg['src']
			# Magic-string "NOENCRYPT" found inside the message
			elif "NOENCRYPT" in msg['src'].longmsg + msg['src'].longmsg_formatted and settings['DEBUG']:
				dbg(c(f"Found magic string 'NOENCRYPT' so not going to encrypt this message {settings['DEBUG']}", 1))
				dst = msg['src']
				dst.longmsg = dst.longmsg.replace("NOENCRYPT", "")
				dst.longmsg_formatted = dst.longmsg_formatted.replace("NOENCRYPT", "")
			elif msg['src'].from_.address == msg['src'].to[0].address:
				dbg(c("Sender == recipient so probably a loopback/test-message, skipping encryption...", 1))
				dst = msg['src']
			else:
				if them['key'] == False:
					dbg("We DO NOT have a key for this recipient")
					# TODO: add policy setting to enforce outbound encryption (allow/deny-list?)
				else:
					dbg("We have a key for this recipient:\n" + prettytable(them['key']))

				dbg(c("Encrypting message...", 2))
				# pEp.unencrypted_subject(True)
				if len(settings['EXTRA_KEYS']) == 0:
					dst = msg['src'].encrypt()
				else:
					dbg("└ with extra key(s): " + ", ".join(settings['EXTRA_KEYS']))
					dst = msg['src'].encrypt(settings['EXTRA_KEYS'], 0)
				dbg(c("Encrypted in", 2), True)

				if settings['DEBUG']:
					dbg("Full dst:\n" + str(dst))
					inspectusingsq(str(dst))

		if settings['mode'] == "decrypt":
			pepfails = False # TODO: store some sort of failure-counter (per message ID?) to detect subsequent failures then fallback to sq, then forward as-is
			if not pepfails:
				dbg(c("Decrypting message via pEp...", 2))
				dst, keys, rating, flags = msg['src'].decrypt()
				dbg(c("Decrypted in", 2), True)
				dst.to = [us['pepid']] # Lower the (potentially rewritten) outer recipient back into the inner message
			else:
				dbg(c("Decrypting message via Sequoia...", 2))
				tmp = decryptusingsq(msg['inmail'], os.path.join(settings['work_dir'], "sec.*.key"))
				dst, keys, rating, flags = pEp.Message(tmp[0]), tmp[1], None, None
				dbg(c("Decrypted in", 2), True)

			# if settings['DEBUG']:
				# dbg("Decrypted message:\n" + c(str(dst), 2))
				# dbg("Keys used: " + ", ".join(keys))
				# dbg("Rating: " + str(rating))
				# dbg("Flags: " + str(flags))

			if str(rating) == "have_no_key":
				keys_path = os.path.join(settings['home'] , settings['keys_dir'])
				dbg(c("No matching key found to decrypt the message. Please put a matching key into the " + c(keys_path, 5) + " folder. It will be sent encrypted to the scanner", 1))
				# exit(7)

			if keys is None or len(keys) == 0:
				dbg(c("Original message was NOT encrypted", 1))
				# TODO: add policy setting to enforce inbound encryption (allow/deny-list?)
			else:
				dbg(c("Original message was encrypted to these keys", 2) + ":\n" + prettytable(list(set(keys))))

		# Workaround for engine converting plaintext-only messages into a msg.txt inline-attachment
		# dst = str(dst).replace(' filename="msg.txt"', "")

	except Exception:
		e = sys.exc_info()
		errmsg  = "ERROR 7: " + str(e[0]) + ": " + str(e[1]) + "\n"
		errmsg += "Traceback:\n" + prettytable([line.strip().replace("\n    ", " ") for line in traceback.format_tb(e[2])])
		dbg(errmsg)
		dbgmail(errmsg)
		exit(7)
		# Alternatively: fall back to forwarding the message as-is
		# dst, keys, rating, flags = src, None, None, None
		# pass

	msg['dst'] = dst
	return msg

# ### Scan pipeline #################################################################################

def filter_message(msg):
	"""
	Run all the commands on the scan_pipeline for the message
	"""
	scanresults = {}
	desc = { 0: "PASS", 1: "FAIL", 2: "RETRY" }
	cols = { 0: 2,      1: 1,      2: 3 }
	for filter in settings['scan_pipes']:
		name = filter['name']
		cmd = filter['cmd']
		if settings['mode'] == "encrypt":
			dbg("Passing original message to scanner " + c(name, 3))
			msgtoscan = str(msg['src'])
		if settings['mode'] == "decrypt":
			dbg("Passing decrypted message to scanner " + c(name, 3))
			msgtoscan = str(msg['dst'])
		try:
			p = Popen(cmd.split(" "), shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
			p.stdin.write(msgtoscan.encode("utf8"))
			stdout, stderr = p.communicate()
			rc = p.returncode
		except Exception:
			rc = 1
			dbg(f"Scanner {name} not available: {rc}")

		if rc in desc.keys():
			scanresults[name] = rc
			dbg("Result: " + c(desc[rc], cols[rc]))
		else:
			dbg("Unknown return code for scanner " + name + ": " + rc)

		if rc == 2:
			dbg(f"Error detected with scanner {name}")
			exit(11)

		if settings['DEBUG']:
			if len(stdout) > 0: dbg(c("STDOUT:\n", 2) + prettytable(stdout.decode("utf8").strip().split("\n")))
			if len(stderr) > 0: dbg(c("STDERR:\n", 1) + prettytable(stderr.decode("utf8").strip().split("\n")))
			# dbg("Return code: " + c(str(rc), 3));

	dbg("Combined scan results:\n" + prettytable(scanresults))

	if sum(scanresults.values()) == 0:
		dbg("All scans " + c("PASSED", 2) + ", relaying message", 2)
	else:
		dbg("Some scans " + c("FAILED", 1) + ", not relaying message (keeping it in the Postfix queue for now)")
		exit(1) # keep message on hold
		# exit(0) # silently drop the message
		# TODO: inform the admin and/or the (likely spoofed) sender


def add_routing_and_headers(pEp, msg, us, them):
	"""
	Complete mail headers with MX routing snd version information
	"""
	global settings
	settings['nextmx'] = None
	opts = {
		"X-pEpGate-mode": settings['mode'],
		"X-pEpGate-version": settings['gate_version'],
		"X-pEpEngine-version": pEp.engine_version,
		"X-NextMX": "auto",
	}

	nextmx_path = os.path.join(settings['home'] , settings['nextmx_map'])
	if settings['mode'] == "encrypt":
		nextmx = jsonlookup(nextmx_path, them['pepid'].address[them['pepid'].address.rfind("@") + 1:], False)

	if settings['mode'] == "decrypt":
		nextmx = jsonlookup(nextmx_path, us['pepid'].address[us['pepid'].address.rfind("@") + 1:], False)

	if nextmx is not None:
		settings['netmx'] = nextmx
		dbg(c("Overriding next MX: " + nextmx, 3))
		opts['X-NextMX'] = nextmx

	opts.update(msg['dst'].opt_fields)
	msg['dst'].opt_fields = opts

	if settings['DEBUG']:
		dbg("Optional headers:\n" + prettytable(msg['dst'].opt_fields), pub=False)

	dst = str(msg['dst'])
	msg['dst'] = dst

	# Log processed message
	logfilename = os.path.join(settings['logpath'], "in." + settings['mode'] + ".processed.eml")
	dbg("p≡p-processed message: " + c(logfilename, 6) + "\n" + str(dst)[0:1337])
	logfile = codecs.open(logfilename, "w", "utf-8")
	logfile.write(dst)
	logfile.close()

	return msg


def deliver_mail(msg):
	"""
	Send outgoing mail
	"""
	dbg("Sending mail via MX: " + (c("auto", 3) if settings['nextmx'] is None else c(str(settings['nextmx']), 1)))
	dbg("From: " + ((c(msg['src'].from_.username, 2)) if len(msg['src'].from_.username) > 0 else "") + c(" <" + msg['src'].from_.address + ">", 3))
	dbg("  To: " + ((c(msg['src'].to[0].username, 2)) if len(msg['src'].to[0].username) > 0 else "") + c(" <" + msg['src'].to[0].address + ">", 3))

	if settings['DEBUG'] and "discard" in msg['src'].to[0].address:
		dbg("Keyword discard found in recipient address, skipping call to sendmail")
	else:
		sendmail(msg['dst'])

	dbg("===== " + c("p≡pGate ended", 1) + " =====")

def log_session():
	"""
	Save per-session logfiles
	"""

	logfilename = os.path.join(settings['logpath'], "debug.log")
	logfile = codecs.open(logfilename, "w", "utf-8")
	logfile.write(getlog("textlog"))
	logfile.close()

	logfilename = os.path.join(settings['logpath'], "debug.html")
	logfile = codecs.open(logfilename, "w", "utf-8")
	logfile.write(getlog("htmllog"))
	logfile.close()
