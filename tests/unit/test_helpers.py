import os
import pytest

from pEphelpers import dbg
from pEphelpers import c
from pEphelpers import toplain
from pEphelpers import tohtml
from pEphelpers import keysfromkeyring
from pEpgate import *

def get_last_line(file_path):
    with open(file_path, 'rb') as f:
        try:  # catch OSError in case of a one line file
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        last_line = f.readline().decode()
    return last_line

def test_dbg():
    dbg("TEST")
    assert 'TEST' in get_last_line(logfilepath)

@pytest.mark.parametrize("text, color, output",
    [
        ("hello world", "1", "\033[1;31mhello world\033[1;m"),
        ("hello world!", "0", "\033[1;30mhello world!\033[1;m"),
        ("hellò wörld!", "3", "\033[1;33mhellò wörld!\033[1;m"),
        ("✨👍🏻", "2", "\033[1;32m✨👍🏻\033[1;m"),
    ])
def test_c(text, color , output):
    assert c(text, color) == output

@pytest.mark.parametrize("output, text",
    [
        ("hello world", "\033[1;31mhello world\033[1;m"),
        ("hello world!", "\033[1;30mhello world!\033[1;m"),
        ("hellò wörld!", "\033[1;33mhellò wörld!\033[1;m"),
        ("✨👍🏻", "\033[1;33m✨👍🏻\033[1;m"),

    ])
def test_toplain(text, output):
    assert toplain(text) == output



@pytest.mark.parametrize("text, output",
    [
        ("\033[1;31mhello world\033[1;m", '<font color="#ff0000">hello&nbsp;world</font>'),
        ("\033[1;30mhello world!\033[1;m", '<font color="#000000">hello&nbsp;world!</font>'),
        ( "\033[1;33mhellò wörld!\033[1;m", '<font color="#ff8800">hellò&nbsp;wörld!</font>'),
        ( "\033[1;33m✨👍🏻\033[1;m", '<font color="#ff8800">✨👍🏻</font>'),

    ])
def test_tohtml(text, output):
    assert tohtml(text) == output


def test_keys_from_keyring_empty(extra_keypair, test_dirs):
    import pEp
    keys = keysfromkeyring()
    assert keys is False

def test_keys_from_keyring(extra_keypair, test_dirs):
    import pEp

    key_file = test_dirs['keys'] / extra_keypair.get_public()
    with open(key_file, "rb") as kf:
        pEp.import_key(kf.read())

    os.chdir(test_dirs['tmp'])
     # keysfromkeyring() will export the keys, so we move to a tmp dir so we don't need to
     # cleanup afterwards
    keys = keysfromkeyring()
    assert extra_keypair.fpr in keys[0]['key_blob']['sq_inspect'][0].replace(' ','')
    assert extra_keypair.fpr == keys[0]['pEp_keys.db']['KeyID']

