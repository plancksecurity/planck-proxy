# Working directory, will be populated with a structure like this:
# ├── <Recipient address>
# │   ├── <Sender address>
# │   │   ├── <Date/Time>
# │   │   │   ├── debug.html
# │   │   │   ├── debug.log
# │   │   │   ├── in.{decrypt|encrypt}.original.eml
# │   │   │   ├── in.{decrypt|encrypt}.parsed.eml
# │   │   │   └── in.{decrypt|encrypt}.processed.eml
# │   │   ├── <Another Date/Time>
# │   │   │   ├── [...]
# │   ├── <Another Sender address>
# │   │   ├── <Date/Time>
# │   │   │   ├── [...]
# │   ├── .pEp
# │   │   ├── keys.db
# │   │   ├── management.db
# │   ├── sec.<recipient address>.key (maybe several)
# │   └── pub.<sender address>.key (likely several)
# ├── <Another Recipient address>
# │   ├── <Sender address>
# │   │   ├── [...]
work_dir       = "work"

# Put the private extra keys in here as *.asc files
keys_dir       = "keys"

# The global logfile
logfile        = "debug.log"

# Forwarding map
#   In encrypt mode: rewrite sender (From: and Reply-To: headers) address or (sub)domain
#   In decrypt mode: rewrite recipient address
forwarding_map = "forwarding.map"

# Username map
#   Cron jobs' senders f.e. tend to contain only ugly username@hostname.tld
#   This adds a nice username to the generated key and optionally also the message itself
username_map   = "username.map"

# NextMX map
#   Statically route specific domains to a specific MX (mainly for testing)
nextmx_map     = "nextmx.map"

# Aliases map
#   Treat multiple (potentially actually) aliased addresses as one and the same sender/recipient/key
aliases_map    = "aliases.map"

# Send failure and debug messages here
admin_addr     = "someone@yourcompany.tld"

# Sender domains that get a debug log when the original message had enabled "Return receipt"
dts_domains    = [ "yourcompany.tld" ]

# Senders that are allowed to use the inline-command RESETKEY/KEYRESET
reset_senders  = [ "service@yourcompany.tld" ]

# Never send encrypted to these domains
never_pEp      = [ "apple.com" ]

# Host and port for the local SMTP server that will handle the emails
SMTP_HOST      = "127.0.0.1"
SMTP_PORT      = 25

# Some test features will only work when DEBUG is on
DEBUG          = False

# Which scans & checks do messages need to pass to be forward
scan_pipeline  = {
	"clamdscan --verbose -z -": { 0: "OK", 1: "FAIL", 2: "TEMPFAIL" },
	"spamc --check -":          { 0: "OK", 1: "FAIL", 5: "TEMPFAIL" }
}

# Extra key used to decrypt messages
EXTRA_KEYS      = [ "1234ABCDEF1234ABCDEF1234ABCDEF1234ABCDEF" ]

# Sequoia command-line tool path (used only in some fallback functions)
sq_bin         = "/usr/local/bin/sq"