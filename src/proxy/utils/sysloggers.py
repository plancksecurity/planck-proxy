import logging
import sys
import os
import time

from proxy.proxy_settings import settings

# Create loggers
console_logger = logging.getLogger('consoleLogger')
file_logger = logging.getLogger('fileLogger')


def get_log_level(level_name):
    """
    Convert a log level name to its corresponding numeric value.

    Args:
        level_name (str): The log level name (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').

    Returns:
        int: The numeric value of the log level.

    Raises:
        ValueError: If the provided level_name is not a valid log level.
    """

    numeric_level = getattr(logging, level_name.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % level_name)

    return numeric_level


def init_logfile(level_name, console_logger, file_logger):
    """
    Initializes loggers with specified log level, handlers, and formatters for both console and file logging.

    Args:
        level_name (str): The log level name (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        console_logger (logging.Logger): Logger for console logging.
        file_logger (logging.Logger): Logger for file logging.

    Returns:
        None
    """

    numeric_level = get_log_level(level_name)
    console_logger.setLevel(level=numeric_level)

    numeric_level = get_log_level(level_name)
    file_logger.setLevel(level=numeric_level)

    # Create handlers
    log_folder = settings['home']
    os.makedirs(log_folder, exist_ok=True)
    log_file = os.path.join(settings['home'], 'planckproxy.log')
    file_handler = logging.FileHandler(log_file)

    # If the command is called by postfix we don't want to ptint to the terminal, otherwise the
    # process will crash with exit code 120.
    if sys.stdout.isatty():
        console_handler = logging.StreamHandler(sys.stdout)
    else:
        console_handler = logging.NullHandler()

    # Set handler levels
    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)

    # Create formatter
    class UTCFormatter(logging.Formatter):
        """
        A custom logging formatter that outputs log records with timestamps in UTC.

        This formatter inherits from logging.Formatter and overrides the formatTime
        method to use UTC time for the timestamps.
        """
        converter = time.gmtime

        def formatTime(self, record, datefmt=None):
            dt = self.converter(record.created)
            if datefmt:
                s = time.strftime(datefmt, dt)
            else:
                t = time.strftime(self.default_time_format, dt)
                s = self.default_msec_format % (t, record.msecs)
            return s

    formatter = UTCFormatter('%(asctime)s.%(msecs)03dZ - %(levelname)s - %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')


    # Set formatter for handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to loggers
    console_logger.addHandler(console_handler)
    file_logger.addHandler(file_handler)
