import os
import argparse
import time
import datetime

def messages_cleanup(work_dir, days, verbose):
    """
    Deletes all files in subfolders of work_dir that were created more than days days ago. If a subfolder in work_dir
    is empty after deleting .eml and .log files, it is also deleted.
    """
    if verbose:
        print(f'Cleaning messages in {work_dir} folder older than {days} days ')

    # Get the current time
    current_time = time.time()

    # Convert days to seconds
    days_in_seconds = days * 24 * 60 * 60

    # Loop through all subfolders in work_dir
    for subdir, dirs, files in os.walk(work_dir):
        # Loop through all files in the current subfolder
        for file in files:
            # Check if the file is an .eml or .log file
            if file.endswith('.eml') or file.endswith('.log'):
                # Get the creation time of the file
                filepath = os.path.join(subdir, file)
                file_modification_time = os.path.getmtime(filepath)

                if verbose:
                    modification_datetime = datetime.datetime.fromtimestamp(file_modification_time)
                    now_datetime = datetime.datetime.now()
                    time_difference = now_datetime - modification_datetime
                    days_since_modification = time_difference.days
                    print(f"The file {filepath} was created {days_since_modification} days ago.")


                # Check if the file was created before the specified number of days
                if current_time - file_modification_time > days_in_seconds:
                    # Delete the file
                    os.remove(filepath)
                    if verbose:
                        print(f"file {filepath} removed")

                else:
                    if verbose:
                        print(f"file {filepath} not old enough, keeping it.")

        # Check if the subfolder is now empty
        if not os.listdir(subdir):
            # Delete the subfolder
            os.rmdir(subdir)
            if verbose:
                print(f"Folder {subdir} is now empty, removing it.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Delete files in subfolders created before a specified number of days')
    parser.add_argument('--work_dir', type=str, default='work_dir', help='the path to the folder containing the subfolders with .eml files')
    parser.add_argument('--days', type=int, default=7, help='the number of days before which to delete the .eml files')
    parser.add_argument('--verbose', '-v', action='store_true', default=False, help='Print output data')
    args = parser.parse_args()

    messages_cleanup(args.work_dir, args.days, args.verbose)



