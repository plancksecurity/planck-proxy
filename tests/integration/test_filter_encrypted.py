# import subprocess
# import os
# import pytest

# @pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
# def test_import_extra_key(test_dirs, extra_keypair):
#     cmd_env = os.environ.copy()
#     cmd_env['work_dir'] = test_dirs['work']
#     cmd_env['keys_dir'] = test_dirs['keys']

#     # Run the command
#     with open(test_dirs['emails'] / 'basic.enc.eml', 'rb') as email:
#         subprocess.run(['./pEpgate decrypt'], shell=True,
#             capture_output=True, input=email.read(), env=cmd_env)

