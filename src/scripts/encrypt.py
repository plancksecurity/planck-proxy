import shutil
import argparse
import os
import re
import email
import sqlite3


def encrypt_msg(msg, our_key, dest_key, extra_key, home_dir, debug):
    """
    Encrypts an email message using p≡p.

    Args:
        msg (str): Path to the email to encrypt.
        our_key (str): Path to the public key of the message sender.
        dest_key (str): Path to the public key of the message recipient.
        extra_key (str): Path to the public extra key.
        home_dir (str): Location of the home folder.
        debug (bool): Keep the home folder and output debug info.

    Returns:
        None
    """
    # Change to pEp home
    home = os.environ.get('HOME')
    if os.path.isdir(home_dir):
        shutil.rmtree(home_dir)
        if debug:
            print(f'previous p≡p directory at {home_dir} erased.')
    if not os.path.isdir(home_dir):
        if debug:
            print(f'p≡p directory created at {home_dir}')
        os.makedirs(home_dir)

    os.environ['HOME'] = home_dir

    import pEp

    if extra_key:
        if debug:
            print('=================')
            print('Extra key')
            print('=================')

        with open(extra_key, 'r') as f:
            key_data = f.read()
        pEp.import_key(key_data)

        if debug:
            print(f'extra_key at {extra_key} successfuly imported')

        keys_db_path = os.path.join(os.environ['HOME'], '.pEp', 'keys.db')
        db = sqlite3.connect(keys_db_path)
        keys = db.execute("SELECT primary_key FROM keys")
        imported_keys = [key[0] for key in keys]
        extra_key_fpr = imported_keys[0]

        if debug:
            print(f'extracted extra_key fingerprint {extra_key_fpr} from the database')

    with open(dest_key, 'r') as f:
        key_data = f.read()
    pEp.import_key(key_data)
    if debug:
        print('=================')
        print('Recipient key')
        print('=================')
        print(f'recipient key at {dest_key} successfuly imported')


    # Encrypt message
    with open(msg, 'r') as f:
        msg = f.read()
    if debug:
        print('=================')
        print('Plain message opened')
        print('=================')
        print(msg)


    if debug:
        print('==========================')
        print('Set our own identity')
        print('==========================')


    mailparseregexes = [
        r"<([\w\-\_\"\.]+@[\w\-\_\"\.{1,}]+)>",
        r"<?([\w\-\_\"\.]+@[\w\-\_\"\.{1,}]+)>?"
    ]

    msgfrom = ""
    mail_obj = email.message_from_string(msg)
    from_headers = mail_obj.get_all("From")

    for mpr in mailparseregexes:
        msgfrom = "-".join(from_headers)
        msgfrom = "-".join(re.findall(re.compile(mpr), msgfrom))
        if len(msgfrom) > 0:
            break

    msgfrom = msgfrom.lower()
    if debug:
        print(f'found our address in the message headers {msgfrom}')

    match = re.match(r'^([^@]+)', msgfrom)
    username = match.group(1)

    with open(our_key, 'r') as f:
        key_data = f.read()
    i = pEp.import_key(key_data)
    our_key_fpr = i[0].fpr

    if debug:
        print(f'our_key at {our_key} successfuly imported with fpr {our_key_fpr}')

    i = pEp.Identity(msgfrom, username)
    pEp.myself(i)


    msg = pEp.Message(msg)
    if extra_key:
        msg = msg.encrypt([extra_key_fpr], 0)
    else:
        msg = msg.encrypt()

    if debug:
        print('=================')
        print('message Encrypted')
        print('=================')
    print(msg)

    if not debug:
        shutil.rmtree(home_dir)

    # Restore home
    os.environ['HOME'] = home


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Encrypts an email message using p≡p")
    parser.add_argument('msg', help='Path to the email to encrypt')
    parser.add_argument('our_key', help='path to the private key of the message sender')
    parser.add_argument('dest_key', help='path to the pub key of the message recipient')
    parser.add_argument('--e', '--extra_key', default=None, help='path to the public extra key')
    parser.add_argument('--m', '--home_dir', default='tmp_home',
                        help='Location of the temporary home folder')
    parser.add_argument('--debug', action='store_true',
                        help='Keep the home folder and output debug info')

    args = parser.parse_args()
    encrypt_msg(args.msg, args.our_key, args.dest_key, args.e, args.m, args.debug)
