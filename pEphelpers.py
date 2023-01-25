from pEpgate import *

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
	try:
		msgfrom, msgto = get_contact_info(msg)
		with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
			server.sendmail(msgfrom, msgto, msg)
	except Exception as e:
		dbg(c(f"ERROR 6 - Mail could not be sent, return code: {e}", 6))
		return False
	else:
		dbg("Mail successfully sent")
		return True

def dbgmail(msg, rcpt=admin_addr, subject="[FATAL] pEp Gate @ " + socket.getfqdn() + " crashed!", attachments=[]):
	# We're in failure-mode here so we can't rely on pEp here and need to hand-craft a MIME-structure
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

# Set variables in the outer scope from within the inner scope "pEpgatemain" (mainly used in cleanup())
def setoutervar(var, val):
	globals()[var] = val

### pEp Sync & echo protocol handling (unused for now) ########################
def messageToSend(msg):
	dbg("Ignoring message_to_send", pub=False)
	# dbg(c("messageToSend(" + str(len(str(msg))) + " Bytes)", 3))
	# dbg(str(msg))

def notifyHandshake(me, partner, signal):
	dbg("Ignoring notify_handshake", pub=False)
	# dbg("notifyHandshake(" + str(me) + ", " + str(partner) + ", " + str(signal) + ")")

def prettytable(thing, colwidth=26):
	ret = ""
	if not isinstance(thing, list):
		thing = [thing]

	for subthing in thing:
		if isinstance(subthing, str):
			ret += (" " * colwidth) + c(" | ", 5) + subthing + "\n"
		elif isinstance(subthing, bool):
			ret += (" " * colwidth) + c(" | ", 5) + str(subthing) + "\n"
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

	# dbg(c("[!!!] Using decryptusingsq() fallback. Attachments will be LOST!", 1))
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
			dbg("CMD: " + " ".join(cmd), pub=False)

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
		msg = email.message_from_string(inmsg)
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
		dbg("ERROR 21 - " + str(e[0]) + ": " + str(e[1]))
		dbg("Traceback: " + str(traceback.format_tb(e[2])))
		return False
		exit(21)

def get_contact_info(inmail):
	"""
	Figure from and to address based on the email headers
	"""

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
		exit(3)

	msgfrom = msgfrom.lower()
	msgto = msgto.lower()

	return msgfrom, msgto

def jsonlookup(jsonmapfile, key, bidilookup=False):
	dbg("JSON lookup in file " + jsonmapfile + " for key " + key)
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

	# Optional: redirect backscatter messages to an admin
	'''
	if jsonmapfile == fwdmappath and result is None:
		dbg("Username part: " + key[:key.rfind("@")])
		if key[:key.rfind("@")] in ("root", "postmaster", "noreply", "no-reply"):
			result = j['default']
			dbg(c("Fallback-rewriting ", 2) + key + " to " + result)
	'''

	return result
