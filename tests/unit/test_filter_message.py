import pytest
import subprocess

from pEpgatemain import filter_message

@pytest.mark.parametrize('collect_email, expected',
    [
        ("basic_filter_evil.eml", 1),
        ("basic.eml", 0)
    ], indirect=['collect_email'])
def test_dummy_filter(collect_email, expected, test_dirs):

    filter_command = test_dirs['root'] / 'dummy_filter.py'
    p1 = subprocess.run(['python', filter_command], input=collect_email)

    assert p1.returncode == expected

@pytest.mark.parametrize('collect_email, expected',
    [
        ("basic_filter_evil.eml", 0),
        ("basic_filter_fail.eml", 1),
        ("basic_filter_retry.eml", 2)
    ], indirect=['collect_email'])
def test_dummy_filter_2(collect_email, expected, test_dirs):

    filter_command = test_dirs['root'] / 'dummy_filter_2.py'
    p1 = subprocess.run(['python', filter_command], input=collect_email)

    assert p1.returncode == expected

@pytest.mark.parametrize('collect_email', ["basic.eml"], indirect=True)
def test_filtering_good(set_settings, test_dirs, collect_email, message):
    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"
    settings = set_settings
    settings['mode']  = 'decrypt'
    settings['scan_pipes']  = [
        {"name": "dummy filter", "cmd": filter_command}
    ]
    message.msg['dst'] = collect_email
    filter_message(message)

@pytest.mark.parametrize('collect_email', ["basic_filter_evil.eml"], indirect=True)
def test_filtering_evil(set_settings, test_dirs, collect_email, message):
    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"
    settings = set_settings
    settings['mode']  = 'decrypt'
    settings['scan_pipes']  = [
        {"name": "dummy filter", "cmd": filter_command}
    ]
    message.msg['dst'] = collect_email

    with pytest.raises(SystemExit) as exec_info:
        filter_message(message)
    assert exec_info.type == SystemExit
    assert exec_info.value.code == 1


@pytest.mark.parametrize('collect_email', ["basic_filter_retry.eml"], indirect=True)
def test_filtering_retry(set_settings, test_dirs, collect_email, monkeypatch, message):

    filter_command = f"python {test_dirs['root'] / 'dummy_filter_2.py'}"
    settings = set_settings
    settings['mode']  = 'decrypt'
    settings['scan_pipes']  = [
        {"name": "dummy filter", "cmd": filter_command}
    ]
    message.msg['dst'] = collect_email

    with pytest.raises(SystemExit) as exec_info:
        filter_message(message)
    assert exec_info.type == SystemExit
    assert exec_info.value.code == 11

@pytest.mark.parametrize('collect_email', ["basic.eml"], indirect=True)
def test_filtering_combined_pass(set_settings, test_dirs, collect_email, message):
    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"
    filter_command_2 = f"python {test_dirs['root'] / 'dummy_filter_2.py'}"
    settings = set_settings
    settings['mode']  = 'decrypt'
    settings['scan_pipes']  = [
        {"name": "dummy filter", "cmd": filter_command},
        {"name": "dummy filter 2", "cmd": filter_command_2}
    ]
    message.msg['dst'] = collect_email
    filter_message(message)

@pytest.mark.parametrize('collect_email', ["basic_filter_evil.eml"], indirect=True)
def test_filtering_combined_fail(set_settings, test_dirs, collect_email, message):
    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"
    filter_command_2 = f"python {test_dirs['root'] / 'dummy_filter_2.py'}"
    settings = set_settings
    settings['mode']  = 'decrypt'
    settings['scan_pipes']  = [
        {"name": "dummy filter", "cmd": filter_command},
        {"name": "dummy filter 2", "cmd": filter_command_2}
    ]
    message.msg['dst'] = collect_email
    with pytest.raises(SystemExit) as exec_info:
        filter_message(message)
    assert exec_info.type == SystemExit
    assert exec_info.value.code == 1
