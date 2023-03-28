import pytest
import subprocess
from update_settings import override_settings


@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_filter_enc_good(test_dirs, extra_keypair, collect_email, cmd_env, settings_file):

    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"

    test_settings = {
        'test-nomails': True,
        'work_dir': str(test_dirs['work']),
        'keys_dir': str(test_dirs['keys']),
        'mode': 'decrypt',
        'scan_pipes': [
            {"name": "dummy filter", "cmd": filter_command}
        ],
        "EXTRA_KEYS": "3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3",
    }
    override_settings(test_dirs['tmp'], test_settings)

    # Run the command
    command = (f"./pEpgate decrypt --settings_file {settings_file}")
    p = subprocess.run([command], shell=True, capture_output=True,
                       input=collect_email, env=cmd_env)

    assert p.returncode is 0


@pytest.mark.parametrize('collect_email', ["basic_filter_evil.enc.eml"], indirect=True)
def test_filter_enc_evil(test_dirs, extra_keypair, collect_email, cmd_env, settings_file):

    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"

    test_settings = {
        'test-nomails': True,
        'work_dir': str(test_dirs['work']),
        'keys_dir': str(test_dirs['keys']),
        'mode': 'decrypt',
        'scan_pipes': [
            {"name": "dummy filter", "cmd": filter_command}
        ],
        "EXTRA_KEYS": "3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3",
    }
    override_settings(test_dirs['tmp'], test_settings)
    command = (f"./pEpgate decrypt --settings_file {settings_file}")
    p = subprocess.run([command], shell=True, capture_output=True,
                       input=collect_email, env=cmd_env)

    assert p.returncode is 1
    assert p.stderr is b''


@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_filter_av_fails(test_dirs, extra_keypair, collect_email, cmd_env, settings_file):

    test_settings = {
        'test-nomails': True,
        'work_dir': str(test_dirs['work']),
        'keys_dir': str(test_dirs['keys']),
        'mode': 'decrypt',
        'scan_pipes': [
            {"name": "broken filter", "cmd": 'no_filter_command'}
        ],
        "EXTRA_KEYS": "3F8B5F3DA55B39F1DF6DE37B6E9B9F4A3035FCE3",
    }

    override_settings(test_dirs['tmp'], test_settings)
    command = (f"./pEpgate decrypt --settings_file {settings_file}")
    p = subprocess.run([command], shell=True, capture_output=True,
                       input=collect_email, env=cmd_env)

    assert p.returncode is 1
    assert p.stderr is b''
