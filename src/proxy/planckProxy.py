#!/usr/bin/env -S python3 -B

import argparse
import atexit
import json
import sys
import logging
import os

# Create loggers
console_logger = logging.getLogger('consoleLogger')
file_logger = logging.getLogger('fileLogger')

from proxy.utils.message import Message
from proxy.utils.hooks import cleanup, except_hook
from proxy.utils.printers import dbg, print_init_info, print_summary_info, print_keys_and_headers
from proxy.utils.logging import init_logging, log_session, init_logfile
from proxy.utils.exporting import init_exporting, export_session

from proxy.proxy_settings import settings, init_settings
from proxy.proxy_main import (
    init_lockfile,
    get_message,
    set_addresses,
    enable_dts,
    init_workdir,
    init_exportdir,
    check_initial_import,
    load_planck,
    import_keys,
    create_planck_message,
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
    init_exportdir(message)

    # Handle keys and decrypt
    import_needed = check_initial_import()
    print_summary_info(message)
    init_logging(message)
    init_exporting(message)
    planck = load_planck()
    if import_needed:
        import_keys(planck)
    print_keys_and_headers(message)
    create_planck_message(planck, message)
    process_message(planck, message)

    # Send to filter
    filter_message(message)

    # Finish processing and deliver
    deliver_mail(message)
    log_session()
    export_session()



def main():
    parser = argparse.ArgumentParser(description="planck Proxy CLI.")
    parser.add_argument("mode", choices=["decrypt"], help="Mode")

    parser.add_argument(
        "settings_file",
        help=('Route for the "settings.json" file.'),
    )

    parser.add_argument(
        "-f",
        "--file",
        default=False,
        help=("Route for the file to analyze."),
    )

    parser.add_argument(
        "-l",
        "--loglevel",
        default="INFO",
        help="Set log legvel, default is INFO.",
    )

    parser.add_argument(
        "--recipients",
        default=False,
        help=("Write down the recipients of the message if Delivered-To header can't be found within the email."),
    )

    # Update the settings dict with the parsed arguments
    cli_args = parser.parse_args()

    for key, val in vars(cli_args).items():
        settings[key] = val

    # Add to the settings dict the settings from the file
    with open(settings["settings_file"], "rb") as f:
        filesettings = json.load(f)

    for setting, value in filesettings.items():
        settings[setting] = value

    init_settings()
    init_logfile(cli_args.loglevel, console_logger, file_logger)

    dbg(f"SETTINGS IMPORTED with 'HOME' as {settings['home']}")
    run_proxy(cli_args)


if __name__ == "__main__":
    main()
