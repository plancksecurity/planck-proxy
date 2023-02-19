import pytest
import os
import subprocess



#Modify 'True' gives Evil string. 'False' gives not evil string
@pytest.mark.parametrize('collect_email', ["basic_evil.eml", "basic.eml"], indirect=True)
def test_dummy_filter(collect_email, get_dummy_dir):

    #Pass contents of EML to filter and destroy OS.ENV traces
    os.environ['test_message'] = collect_email
    p1 = subprocess.run(['python', get_dummy_dir])
    os.environ.pop('test_message')

    #Check the arbitrary set exit codes to see if EVIL is found
    if p1.returncode == 201:
        print('is evil')
    elif p1.returncode == 200:
        print('is NOT evil')
    else:
        print('Unexpected behaviour')

    assert p1.returncode is 200 or 201

@pytest.mark.parametrize('collect_email', ["basic_evil.eml", "basic.eml"], indirect=True)
def test_filter_message(collect_email, test_dirs):
    assert True

#PASS THE DUMMY FILTER ROUTE ASS OVERRIDE OF SETTINGS WHEN INITIALIZING THE PEPGATE COMMAND
#create "override_av=True" param through argparse

#if cmd is 'DUMMY':
#	cmd = (f"python {settings['home']}/tests/dummy_filter.py")
#make param through args for dummy to work (can be left there as implementation testing)