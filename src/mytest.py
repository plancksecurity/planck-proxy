#!/usr/bin/env -S python3 -B

import argparse
import atexit

from pEphelpers import get_default, cleanup, except_hook
from pEpgatesettings import settings, init_settings
from pEpgatemain import *

from dataclasses import dataclass, field




def init_person():
     return {
          'addr': None,
          'key': None,
          'keyname': None,
          'keyaddr': None,
          'keyfpr': None,
          'pepid': None,
    }

def init_msg():
    return {
          'inmail': None,
          'msgfrom': None,
          'msgto': None,
          'src': None, # pEp Message
          'dst': None,
    }

@dataclass
class Message:
    msg: dict = field(default_factory=init_msg)
    us: dict = field(default_factory=init_person)
    them: dict = field(default_factory=init_person)


def main():

    message = Message()

    print(message)

if __name__ == '__main__':
	main()
