"""This dummy filter searches for 'EVIL' in a given string and outputs 0 or 1 as required"""

import sys

def main():
    test_message = ''.join(sys.stdin.readlines())
    if 'FAIL' in test_message:
        sys.exit(1)
    if 'RETRY' in test_message:
        sys.exit(2)

    sys.exit(0)

if __name__ == '__main__':
    main()
