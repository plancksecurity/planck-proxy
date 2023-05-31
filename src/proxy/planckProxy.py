#!/usr/bin/env -S python3 -B

import argparse
import atexit
import json
import sys


from proxy.utils.message import Message
from proxy.utils.hooks import cleanup, except_hook
from proxy.utils.parsers import get_default
from proxy.utils.printers import dbg, print_init_info, print_summary_info, print_keys_and_headers
from proxy.utils.logging import init_logging, log_session

from .proxy_settings import settings, init_settings
from .proxy_main import (
    init_lockfile,
    get_message,
    set_addresses,
    enable_dts,
    init_workdir,
    check_initial_import,
    load_pep,
    import_keys,
    create_pEp_message,
    process_message,
    filter_message,
    deliver_mail,
)


def run_proxy(cli_args):
    """
    Command which runs all the code logic
    Args:
        cli_args (argparse.Namespace): Arguments.

    Returns:
        None
    """
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
    # addr_domain_rewrite(message)
    init_workdir(message)

    # Handle keys and decrypt
    import_needed = check_initial_import()
    print_summary_info(message)
    init_logging(message)
    pEp = load_pep()
    if import_needed:
        import_keys(pEp)
    print_keys_and_headers(message)
    create_pEp_message(pEp, message)
    process_message(pEp, message)

    # Send to filter
    filter_message(message)

    # Finish processing and deliver
    deliver_mail(message)
    log_session()


def main():
    # init_settings to import data from the settings.json into the global settings dict
    init_settings()
    dbg(f"SETTINGS IMPORTED with 'HOME' as {settings['home']}")

    # Parse the settings from the CLI, or get some default vaulues from the env if the argument is not provided
    # Parsed settings will be:
    # 1 - The param provided
    # 2 - Env with the setting name in the OS
    # 3 - Default value in the settings global var

    parser = argparse.ArgumentParser(description="planck Proxy CLI.")
    parser.add_argument("mode", choices=["decrypt"], help="Mode")
    parser.add_argument(
        "--DEBUG",
        action="store_true",
        default=get_default("DEBUG", type=bool),
        help=f'Set DEBUG mode, default is {get_default("DEBUG")}',
    )
    parser.add_argument(
        "--keys_dir",
        default=get_default("keys_dir"),
        help=f'Directory where the extra key should be imported from, default is "{get_default("keys_dir")}"',
    )
    parser.add_argument(
        "--work_dir",
        default=get_default("work_dir"),
        help=f'Directory where the command outputs are placed, default is "{get_default("work_dir")}"',
    )
    parser.add_argument(
        "--SMTP_HOST",
        default=get_default("SMTP_HOST"),
        help=f'Address of the SMTP host used to send the messages. Default "{get_default("SMTP_HOST")}"',
    )
    parser.add_argument(
        "--SMTP_PORT",
        type=int,
        default=get_default("SMTP_PORT"),
        help=f'Port of the SMTP host used to send the messages. Default "{get_default("SMTP_PORT")}"',
    )
    parser.add_argument(
        "--settings_file",
        help=('Provides a route to a different "settings.json" file.'),
        default=None,
    )

    # Update the settings dict with the parsed arguments
    cli_args = parser.parse_args()
    for key, val in vars(cli_args).items():
        settings[key] = val

    # if a settings file is provided, use it to overwrite the settings dict
    if settings["settings_file"] is not None:
        with open(settings["settings_file"], "rb") as f:
            filesettings = json.load(f)

        for setting, value in filesettings.items():
            settings[setting] = value

    if cli_args.DEBUG:
        settings["DEBUG"] = True

    run_proxy(cli_args)


if __name__ == "__main__":
    main()
