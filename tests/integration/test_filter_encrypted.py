import pytest
import subprocess


##TO DO -- REVAMP INTO NEW SETTINGS METHODOLOGY

@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_filter_enc_good(test_dirs, extra_keypair, collect_email):

    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"
    test_settings = {}
    test_settings['test-nomails']  = True
    test_settings['work_dir'] = str(test_dirs['work'])
    test_settings['keys_dir'] = str(test_dirs['keys'])
    test_settings['mode']  = 'decrypt'
    test_settings['scan_pipes']  = [{"name": "dummy filter", "cmd": filter_command}]

    command = f'python ./src/scripts/_gate_test_runner.py "{str(test_settings)}"'
    p = subprocess.run([command], shell=True, capture_output=True, input=collect_email)

    assert p.returncode is 0


@pytest.mark.parametrize('collect_email', ["basic_filter_evil.enc.eml"], indirect=True)
def test_filter_enc_evil(test_dirs, extra_keypair, collect_email):

    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"
    test_settings = {}
    test_settings['test-nomails']  = True
    test_settings['work_dir'] = str(test_dirs['work'])
    test_settings['keys_dir'] = str(test_dirs['keys'])
    test_settings['mode']  = 'decrypt'
    test_settings['scan_pipes']  = [{"name": "dummy filter", "cmd": filter_command}]

    command = f'python ./src/scripts/_gate_test_runner.py "{str(test_settings)}"'
    p = subprocess.run([command], shell=True, capture_output=True, input=collect_email)

    assert p.returncode is 1
    assert p.stderr is b''


@pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
def test_filter_av_fails(test_dirs, extra_keypair, collect_email):

    test_settings = {}
    test_settings['test-nomails']  = True
    test_settings['work_dir'] = str(test_dirs['work'])
    test_settings['keys_dir'] = str(test_dirs['keys'])
    test_settings['mode']  = 'decrypt'
    test_settings['scan_pipes']  = [{"name": "broken filter", "cmd": "no_filter_command"}]

    command = f'python ./src/scripts/_gate_test_runner.py "{str(test_settings)}"'
    p = subprocess.run([command], shell=True, capture_output=True, input=collect_email)

    assert p.returncode is 1
    assert p.stderr is b''
