import shutil
import argparse
import os


def encrypt_msg(msg, dest_key, extra_key, extra_key_fpr, home_dir, debug):
    """
    Encrypts an email message using p≡p.

    Args:
        msg (str): Path to the email to encrypt.
        dest_key (str): Public key of the message recipient.
        extra_key (str): Public extra key.
        extra_key_fpr (str): Fingerprint of the extra key.
        home_dir (str): Location of the home folder.
        debug (bool): Keep the home folder and output debug info.

    Returns:
        None
    """
    # Change to pEp home
    home = os.environ.get('HOME')
    if not os.path.isdir(home_dir):
        if debug:
            print(f'p≡p directory created at {home_dir}')
        os.makedirs(home_dir)

    os.environ['HOME'] = home_dir
    import pEp

    if dest_key:
        with open(dest_key, 'r') as f:
            key_data = f.read()
        pEp.import_key(key_data)
        if debug:
            print(f'recipient key at {dest_key} successfuly imported')

    if extra_key:
        with open(extra_key, 'r') as f:
            key_data = f.read()
        pEp.import_key(key_data)
        if debug:
            print(f'extra_key at {extra_key} successfuly imported')

    # Encrypt message
    with open(msg, 'r') as f:
        msg = f.read()
    if debug:
        print('=================')
        print('Plain message')
        print('=================')
        print(msg)

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
    parser = argparse.ArgumentParser()
    parser.add_argument('msg', help='Path to the email to encrypt')
    parser.add_argument('--d', '--dest_key', default=None,
                        help='pub key of the message recipient')
    parser.add_argument(
        '--e', '--extra_key', default='../../tests/test_keys/3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3.pub.asc', help='pub extra key')
    parser.add_argument(
        '--f', '--fpr', default='3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3', help='fpr of the extra key')
    parser.add_argument('--m', '--home_dir', default='tmp_home',
                        help='Location of the home folder')
    parser.add_argument('--debug', action='store_true',
                        help='Keep the home folder and output debug info')

    args = parser.parse_args()
    encrypt_msg(args.msg, args.d, args.e, args.f, args.m, args.debug)
