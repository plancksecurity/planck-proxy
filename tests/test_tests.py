"""
This file contains some self-tests for the test-suite.
"""

import os
import pytest


def test_home(tmp_path_factory):
    """
    Ensure HOME points to the base directory for this test session.
    """
    home = tmp_path_factory.getbasetemp()
    if os.getenv("HOME") != str(home):
        pytest.exit("self-test failed: HOME does not point to temp dir", 1)
