"""
This file contains some self-tests for the test-suite.
"""

import os
import pytest


# def test_home(tmp_path_factory):
#     """
#     Ensure HOME points to the base directory for this test session.
#     """
#     home = tmp_path_factory.getbasetemp()
#     if os.getenv("HOME") != str(home):
#         pytest.exit("self-test failed: HOME does not point to temp dir", 1)

# def test_pEp_user_directory(tmp_path_factory):
#     """
#     Ensure pEp.per_user_directory points to the base directory for
#     this test session - or to PEP_HOME, if that is set.
#     """
#     import pEp  # late import for safety
#     pep_folder = pEp.per_user_directory
#     home = tmp_path_factory.getbasetemp()
#     if os.getenv("PEP_HOME"):
#         home = pathlib.Path(os.getenv("PEP_HOME"))
#     if pep_folder != str(home / ".pEp"):
#         pytest.exit("self-test failed: per_user_directory is not in temp dir", 1)
