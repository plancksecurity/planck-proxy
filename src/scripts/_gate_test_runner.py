"""
Helper to run the pEpgate sript with any given settings and not being dependant
on the argparse for test-only stuff
"""

import argparse
import ast
import sys, os
from pathlib import Path

# We can't import a parent module unless it's in sys.path
SRC_PATH = Path(os.path.dirname(__file__)).parent
ROOT_PATH = SRC_PATH.parent
sys.path.append(str(SRC_PATH.resolve()))

from pEpgatesettings import settings, init_settings
from pEpgate import main

def run(test_settings):
    # Collect the original settings
    init_settings()

    #Overwrite them with the test settings
    for key,val in test_settings.items():
        settings[key] = val

    # We need to correct the 'home' since this file is one level deeper in
    # the system tree than pEpgatesettings.py
    settings['home'] = str(ROOT_PATH.resolve())

    main([])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pEp Proxy test runner.')
    parser.add_argument('test_settings', help='Settings')
    cli_args = parser.parse_args()
    test_settings = ast.literal_eval(cli_args.test_settings)
    run(test_settings)
