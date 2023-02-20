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
    p1 = subprocess.run(['python', filter_command], input=collect_email.encode('utf-8'))

    assert p1.returncode == expected

@pytest.mark.parametrize('collect_email, expected',
    [
        ("basic_filter_evil.eml", 0),
        ("basic_filter_fail.eml", 1),
        ("basic_filter_retry.eml", 2)
    ], indirect=['collect_email'])
def test_dummy_filter_2(collect_email, expected, test_dirs):

    filter_command = test_dirs['root'] / 'dummy_filter_2.py'
    p1 = subprocess.run(['python', filter_command], input=collect_email.encode('utf-8'))

    assert p1.returncode == expected

@pytest.mark.parametrize('collect_email', ["basic.eml"], indirect=True)
def test_filtering_good(settings, test_dirs, collect_email):
    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"
    settings['mode']  = 'decrypt'
    settings['scan_pipes']  = [
        {"name": "dummy filter", "cmd": filter_command}
    ]
    msg = {'dst': collect_email}
    filter_message(msg)

@pytest.mark.parametrize('collect_email', ["basic_filter_evil.eml"], indirect=True)
def test_filtering_evil(settings, test_dirs, collect_email):
    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"
    settings['mode']  = 'decrypt'
    settings['scan_pipes']  = [
        {"name": "dummy filter", "cmd": filter_command}
    ]
    msg = {'dst': collect_email}
    with pytest.raises(SystemExit) as exec_info:
        filter_message(msg)
    assert exec_info.type == SystemExit
    assert exec_info.value.code == 1


@pytest.mark.parametrize('collect_email', ["basic_filter_retry.eml"], indirect=True)
def test_filtering_retry(settings, test_dirs, collect_email, monkeypatch):
    # dbgmail needs to be mocked otherwise the send method call crashes the test
    # TODO: maybe mock send() globally in a fixture
    # TODO: maybe do the same for dbg() so we don't pollute the logs while testing
    import pEpgatemain
    def mock_dbgmail(msg):
        return True
    monkeypatch.setattr(pEpgatemain, "dbgmail", mock_dbgmail)

    filter_command = f"python {test_dirs['root'] / 'dummy_filter_2.py'}"
    settings['mode']  = 'decrypt'
    settings['scan_pipes']  = [
        {"name": "dummy filter", "cmd": filter_command}
    ]
    msg = {'dst': collect_email}
    with pytest.raises(SystemExit) as exec_info:
        filter_message(msg)
    assert exec_info.type == SystemExit
    assert exec_info.value.code == 11

@pytest.mark.parametrize('collect_email', ["basic.eml"], indirect=True)
def test_filtering_combined_pass(settings, test_dirs, collect_email):
    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"
    filter_command_2 = f"python {test_dirs['root'] / 'dummy_filter_2.py'}"
    settings['mode']  = 'decrypt'
    settings['scan_pipes']  = [
        {"name": "dummy filter", "cmd": filter_command},
        {"name": "dummy filter 2", "cmd": filter_command_2}
    ]
    msg = {'dst': collect_email}
    filter_message(msg)

@pytest.mark.parametrize('collect_email', ["basic_filter_evil.eml"], indirect=True)
def test_filtering_combined_fail(settings, test_dirs, collect_email):
    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"
    filter_command_2 = f"python {test_dirs['root'] / 'dummy_filter_2.py'}"
    settings['mode']  = 'decrypt'
    settings['scan_pipes']  = [
        {"name": "dummy filter", "cmd": filter_command},
        {"name": "dummy filter 2", "cmd": filter_command_2}
    ]
    msg = {'dst': collect_email}
    with pytest.raises(SystemExit) as exec_info:
        filter_message(msg)
    assert exec_info.type == SystemExit
    assert exec_info.value.code == 1
