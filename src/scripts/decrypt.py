
import argparse
import os


def decrypt_msg(msg, key, home_dir, debug):
    """
    Decrypt a message using p≡p.

    Args:
        msg (str): Path to the email to decrypt.
        key (str): Path to the key to decrypt.
        home_dir (str): Location of the home folder.
        debug (bool): Output debug info.

    Returns:
        None
    """
    # Change to pEp home
    home = os.environ.get('HOME')
    if not os.path.isdir(home_dir):
        print(f'p≡p directory created at {home_dir}')
        os.makedirs(home_dir)

    os.environ['HOME'] = home_dir
    import pEp

    # Import key
    if key:
        with open(key, 'r') as f:
            key_data = f.read()
        pEp.import_key(key_data)
        print(f'key at {key} successfuly imported')

    # Decrypt message
    with open(msg, 'r') as f:
        msg = f.read()
    if debug:
        print('=================')
        print('message encrypted')
        print('=================')
        print(msg)

    msg = pEp.Message(msg)
    msg, keys, rating, flags = msg.decrypt()

    if debug:
        print('=================')
        print('message Decrypted')
        print('=================')
    print(msg)

    # Restore home
    os.environ['HOME'] = home


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('msg', help='Path to the email to decrypt')
    parser.add_argument('--key', default=None, help='key to decrypt')
    parser.add_argument('--m', '--home_dir', default='tmp_home',
                        help='Location of the home folder')
    parser.add_argument('--debug', action='store_true',
                        help='Keep the home folder and output debug info')

    args = parser.parse_args()
    decrypt_msg(args.msg, args.key, args.m, args.debug)
