#!/usr/bin/env -S python3 -B

import argparse
import atexit

from pEphelpers import get_default, cleanup, except_hook
from pEpgatesettings import settings, init_settings
from pEpgatemain import *

from dataclasses import dataclass, field

def init_msg():
    return {
          'inmail': None,
          'msgfrom': None,
          'msgto': None,
          'src': None, # pEp Message
          'dst': None, # pEp Message
    }

def init_person():
     return {
          'addr': None,
          'key': None,
          'keyname': None,
          'keyaddr': None,
          'keyfpr': None,
          'pepid': None, # pEp Identity
    }
@dataclass
class Message:
    msg: dict = field(default_factory=init_msg)
    us: dict = field(default_factory=init_person)
    them: dict = field(default_factory=init_person)


def main(cli_args):

	# Setup
	atexit.register(cleanup)
	sys.excepthook = except_hook
	message = Message()

	# Init
	print_init_info(cli_args)
	init_lockfile()

	# Get message and check recipients
	get_message(message)
	set_addresses(message)
	enable_dts(message)
	addr_domain_rewrite(message)
	init_workdir(message)

	# Handle keys and encrypt/decrypt
	check_key_reset(message)
	import_needed = check_initial_import()
	print_summary_info(message)
	init_logging(message)
	pEp = load_pep()
	if import_needed:
		import_keys(pEp)
	print_keys_and_keaders(message)
	if settings['mode'] == 'encrypt':
		check_recipient_pubkey(pEp, message)
	check_sender_privkey(message)
	set_own_identity(pEp, message)
	create_pEp_message(pEp, message)
	process_message(pEp, message)

	# Send to filter
	filter_message(message)

	# Finish processing and deliver
	add_routing_and_headers(pEp, message)
	deliver_mail(message)
	log_session()

if __name__ == '__main__':

	init_settings()
	dbg(f"SETTINGS IMPORTED with 'HOME' as {settings['home']} and 'DTS' as {settings['dts']}")

	parser = argparse.ArgumentParser(description='pEp Proxy CLI.')
	parser.add_argument('mode', choices=["encrypt", "decrypt"], help='Mode')
	parser.add_argument('--DEBUG', action='store_true',
		default=get_default("DEBUG", type=bool), help=f'Set DEBUG mode, default is {get_default("DEBUG")}')
	parser.add_argument('--EXTRA_KEYS', nargs='*', default=get_default("EXTRA_KEYS", type=list),
		help=f'Space-separated fingerprint(s) to use as extra key(s) when encrypting messages, default is "{get_default("EXTRA_KEYS")}"')
	parser.add_argument('--keys_dir', default=get_default("keys_dir"),
		help=f'Directory where the extra key should be imported from, default is "{get_default("keys_dir")}"')
	parser.add_argument('--work_dir', default=get_default("work_dir"),
		help=f'Directory where the command outputs are placed, default is "{get_default("work_dir")}"')
	parser.add_argument('--SMTP_HOST', default=get_default("SMTP_HOST"),
		help=f'Address of the SMTP host used to send the messages. Default "{get_default("SMTP_HOST")}"')
	parser.add_argument('--SMTP_PORT', type=int, default=get_default("SMTP_PORT"),
		help=f'Port of the SMTP host used to send the messages. Default "{get_default("SMTP_PORT")}"')
	parser.add_argument('--settings_file', help=('Provides a route to a different "settings.json" file.'), default=None)

	cli_args = parser.parse_args()
	for key,val in vars(cli_args).items():
		settings[key] = val

	if settings['settings_file'] is not None:
		with open(settings['settings_file'], "rb") as f:
			filesettings = json.load(f)

		for setting, value in filesettings.items():
			settings[setting] = value

	main(cli_args)
