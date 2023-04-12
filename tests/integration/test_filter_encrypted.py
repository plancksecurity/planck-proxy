import pytest
import subprocess
from override_settings import override_settings


@pytest.mark.parametrize("collect_email", ["basic.enc.eml"], indirect=True)
def test_filter_enc_good(test_dirs, extra_keypair, collect_email, settings_file, test_settings_dict):
    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"

    test_settings_dict["scan_pipes"] = [{"name": "dummy filter", "cmd": filter_command}]

    settings_file = override_settings(test_dirs, settings_file, test_settings_dict)

    # Run the command
    command = f"./pEpgate decrypt --settings_file {settings_file}"
    p = subprocess.run([command], shell=True, capture_output=True, input=collect_email)

    assert p.returncode == 0


@pytest.mark.parametrize("collect_email", ["basic_filter_evil.enc.eml"], indirect=True)
def test_filter_enc_evil(test_dirs, extra_keypair, collect_email, settings_file, test_settings_dict):
    filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"

    test_settings_dict["scan_pipes"] = [{"name": "dummy filter", "cmd": filter_command}]
    settings_file = override_settings(test_dirs, settings_file, test_settings_dict)

    command = f"./pEpgate decrypt --settings_file {settings_file}"
    p = subprocess.run([command], shell=True, capture_output=True, input=collect_email)

    assert p.returncode == 1
    assert p.stderr == b""


@pytest.mark.parametrize("collect_email", ["basic.enc.eml"], indirect=True)
def test_filter_av_fails(test_dirs, extra_keypair, collect_email, settings_file, test_settings_dict):
    test_settings_dict["scan_pipes"] = [{"name": "broken filter", "cmd": "no_filter_command"}]

    settings_file = override_settings(test_dirs, settings_file, test_settings_dict)

    command = f"./pEpgate decrypt --settings_file {settings_file}"
    p = subprocess.run([command], shell=True, capture_output=True, input=collect_email)

    assert p.returncode == 1
    assert p.stderr == b""
