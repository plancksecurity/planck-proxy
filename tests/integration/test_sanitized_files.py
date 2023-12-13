import subprocess
import os
import pytest
from proxy.utils.parsers import get_contact_info
from proxy.utils.sanitizer import sanitize_email_address
from override_settings import override_settings


@pytest.mark.parametrize("collect_email", ["basic_unsanitized.eml"], indirect=True)
def test_sanitized_files(
    set_settings,
    settings_file,
    test_dirs,
    collect_email,
    extra_keypair,
    test_settings_dict,
):
    email = collect_email.decode()
    test_email_from, test_email_to = get_contact_info(email)
    settings_file = override_settings(test_dirs, settings_file, test_settings_dict)

    command = f"planckproxy decrypt {settings_file}"
    p = subprocess.run([command], shell=True, capture_output=True, input=collect_email)
    #assert p.stderr == b""
    #assert p.returncode == 0
    

    decrypt_out_path = test_dirs["work"] / sanitize_email_address(test_email_to) / sanitize_email_address(test_email_from)
    assert os.listdir(decrypt_out_path)