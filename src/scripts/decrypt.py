
import argparse
import os


def decrypt_msg(msg, key, home_dir):
    """
    Decrypt a message using p≡p.

    Args:
        msg: Path to the email to decrypt.
        key: Key to decrypt.
        home_dir: Location of the home folder.

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
    print('=================')
    print('message encrypted')
    print('=================')
    print(msg)

    msg = pEp.Message(msg)
    msg, keys, rating, flags = msg.decrypt()

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

    args = parser.parse_args()
    decrypt_msg(args.msg, args.key, args.m)
