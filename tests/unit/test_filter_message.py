import pytest
import subprocess


@pytest.mark.parametrize('collect_email, expected',
    [
        ("basic_evil.eml", 201),
        ("basic.eml", 200)
    ], indirect=['collect_email'])
def test_dummy_filter(collect_email, expected, test_dirs):

    filter_command = test_dirs['root'] / 'dummy_filter.py'
    p1 = subprocess.run(['python', filter_command], input=collect_email.encode('utf-8'))

    assert p1.returncode == expected
