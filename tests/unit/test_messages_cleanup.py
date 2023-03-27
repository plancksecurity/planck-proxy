import os
import time
import pytest
from src.scripts.messages_cleanup import messages_cleanup
import os

def mod_timestamp(file, days):
    os.utime(file, (time.time() - days * 24 * 60 * 60, time.time() - days * 24 * 60 * 60))

def test_messages_cleanup(test_dirs):
    work_dir = test_dirs['tmp']

    subdir1 = work_dir / 'subdir1'
    subdir1.mkdir(parents=True)
    file1 = subdir1 / 'file1.eml'
    file2 = subdir1 / 'file2.log'
    (file1).touch()
    (file2).touch()
    mod_timestamp(file1, 8)
    mod_timestamp(file2, 8)

    subdir2 = work_dir / 'subdir2'
    subdir2.mkdir(parents=True)
    file3 = subdir2 / 'file3.eml'
    file4 = subdir2 / 'file4.log'
    file5 = subdir2 / 'file5.test'
    (file3).touch()
    (file4).touch()
    (file5).touch()
    mod_timestamp(file3, 8)
    mod_timestamp(file4, 8)
    mod_timestamp(file5, 8)

    subdir3 = work_dir / 'subdir3'
    subdir3.mkdir(parents=True)
    file6 = subdir3 / 'file6.eml'
    file7 = subdir3 / 'file7.log'
    file8 = subdir3 / 'file8.log'
    (file6).touch()
    (file7).touch()
    (file8).touch()
    mod_timestamp(file6, 6)
    mod_timestamp(file7, 6)
    mod_timestamp(file8, 6)

    messages_cleanup(str(work_dir), 7, True)

    assert os.path.exists(subdir1) == False
    assert os.path.exists(file1) == False
    assert os.path.exists(file2) == False

    assert os.path.exists(subdir2) == True
    assert os.path.exists(file3) == False
    assert os.path.exists(file4) == False
    assert os.path.exists(file5) == True

    assert os.path.exists(subdir3) == True
    assert os.path.exists(file6) == True
    assert os.path.exists(file7) == True
    assert os.path.exists(file8) == True
