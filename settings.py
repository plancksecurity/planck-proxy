# Working directory, will be populated with a structure like this:
# ├── <Recipient address>
# │   ├── <Sender address>
# │   │   ├── <Date/Time>
# │   │   │   ├── debug.html
# │   │   │   ├── debug.log
# │   │   │   ├── in.{decrypt|encrypt}.original.eml
# │   │   │   ├── in.{decrypt|encrypt}.parsed.eml
# │   │   │   └── in.{decrypt|encrypt}.processed.eml
# │   │   ├── <Anbother Date/Time>
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
admin_addr     = "aw@pep.security"

# Sender domains that get a debug log when the original message had enabled "Return receipt"
dts_domains    = [ "peptest.ch", "pep.security", "0x3d.lu" ]

# Senders that are allowed to use the inline-command RESETKEY/KEYRESET
reset_senders  = [ "support@pep.security", "contact@pep.security", "it@pep.security" ]

# Never send encrypted to these domains
never_pEp      = [ "apple.com" ]

# Host and port for the local SMTP server that will handle the emails
SMTP_HOST  = "80.90.47.12"
SMTP_PORT = 25

DEBUG = False
