import pytest
import string

from proxy.utils.sanitizer import sanitize_email_address

def test_sanitize_address():
    allowed_chars = set(string.ascii_lowercase + string.digits + '-' + '.' + '_' + '@')
    test_email = "a$_technically_/valid-=email!@gmail.com"

    sanitized_address = sanitize_email_address(test_email)

    is_sanitized = set(sanitized_address) <= allowed_chars
    assert is_sanitized

