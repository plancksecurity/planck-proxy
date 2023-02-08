#!/usr/bin/env -S python3 -B
# import codecs
# import random

# from uuid        import uuid4
# from shutil      import copytree
import argparse
import atexit
import tomli

from .pEphelpers import get_default, cleanup
from .pEpgatesettings import settings, init_settings
from .pEpgatemain import print_init_info, init_lockfile, get_message, set_addresses, enable_dts

def main():

	with open("./settings.toml", "rb") as f:
		filesettings = tomli.load(f)

	init_settings(filesettings)
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

	print_init_info(args)
	init_lockfile()

	inmail = get_message()
	ouraddr, theiraddr = set_addresses(inmail)
	enable_dts(inmail)

	print(ouraddr, theiraddr)


