import os
import sys

#This dummy filter searches for 'EVIL' in a given string and outputs 0 or 1 as required

#NEEDS TO BE CHANGED TO STDIN

def main():
    test_message = os.environ.get('test_message')

    if 'EVIL' in test_message:
        sys.exit(201)
    
    sys.exit(200)


if __name__ == '__main__':
    main()