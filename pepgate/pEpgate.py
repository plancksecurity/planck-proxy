#!/usr/bin/env -S python3 -B

import argparse
import atexit
import tomli

from .pEphelpers import get_default, cleanup
from .pEpgatesettings import settings, init_settings
from .pEpgatemain import *

def main():
	init_settings()
	atexit.register(cleanup)

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
		settings[key] = val


	msg = {}
	us = {}
	them = {}

	print_init_info(args)
	init_lockfile()
	msg = get_message(msg)
	msg, us, them = set_addresses(msg, us, them)
	enable_dts(msg)
	msg = check_key_reset(msg, us, them)
	us = addr_domain_rewrite(us)
	init_workdir(us)
	import_needed = check_initial_import()
	print_summary_info(msg, us, them)
	init_logging(msg, them)
	pEp = load_pep()
	if import_needed:
		import_keys(pEp)
	print_keys_and_keaders(msg)
	if settings['mode'] == 'encrypt':
		them = check_recipient_pubkey(pEp, them)
	us = check_sender_privkey(us)
	us = set_own_identity(pEp, us)
	msg = create_pEp_message(pEp, msg, us, them)
	msg = process_message(pEp, msg, us, them)
	filter_message(msg)
	msg = add_routing_and_headers(pEp, msg, us, them)
	deliver_mail(msg)
	log_session()



