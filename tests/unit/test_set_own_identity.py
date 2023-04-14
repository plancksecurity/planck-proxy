# import os
# import pytest

# from src.pEpgatemain import set_own_identity
# from tests.conftest import MockpEpMessage, MockpEpId


# def test_set_own_identity_no_existing_key_existing_username(set_settings, test_dirs, pEp, message):
#     settings = set_settings
#     settings["mode"] = "decrypt"
#     settings["work_dir"] = str(test_dirs["work"])
#     settings["home"] = str(test_dirs["root"])
#     settings["nextmx_map"] = test_dirs["root"] / "tests_settings" / "username.map"

#     message = MockpEpMessage()
#     # Set the message.us dictionary
#     message.us = {"addr": "test@example.com", "keyname": None, "keyaddr": None, "keyfpr": None}


#     # Call the function
#     set_own_identity(pEp, message)

#     # Check that pEp.Identity was called with the expected arguments
#     expected_identity = pEp.Identity("test@example.com", "test at example dot com")
#     assert pEp.Identity.call_args_list == [((expected_identity.addr, expected_identity.username), {})]

#     # Check that pEp.myself was called with the expected argument
#     assert pEp.myself.call_args_list == [((expected_identity,), {})]

#     # Check that message.us["pepid"] is set to the expected value
#     assert message.us["pepid"] == expected_identity


# def test_set_own_identity_existing_key(pEp, message):
#     # Mock the settings dictionary
#     settings = {"home": "/path/to/home", "username_map": "username.map"}

#     # Set the message.us dictionary
#     message.us = {
#         "addr": "test@example.com",
#         "keyname": "Test Key",
#         "keyaddr": "test@example.com",
#         "keyfpr": "ABCDEF1234567890",
#     }

#     # Set the username_map_path
#     username_map_path = os.path.join(settings["home"], settings["username_map"])

#     # Mock the jsonlookup function
#     def mock_jsonlookup(path, key, default):
#         if key == "test@example.com":
#             return "Test User"
#         else:
#             return None

#     # Replace the real jsonlookup function with the mock function
#     with patch("your_module.jsonlookup", side_effect=mock_jsonlookup):
#         # Call the function
#         set_own_identity(pEp, message)

#     # Check that pEp.Identity was called with the expected arguments
#     expected_identity = pEp.Identity("test@example.com", "Test User")
#     assert pEp.Identity.call_args_list == [((expected_identity.addr, expected_identity.username), {})]

#     # Check that pEp.myself was called with the expected argument
#     assert pEp.myself.call_args_list == [((expected_identity,), {})]

#     # Check that message.us["pepid"] is set to the expected value
#     assert message.us["pepid"] == expected_identity
