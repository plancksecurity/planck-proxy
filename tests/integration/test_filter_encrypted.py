# import os
# import pytest

# import pEpgate

# @pytest.mark.parametrize('collect_email', ["basic.enc.eml"], indirect=True)
# def test_filter_enc_good(settings, test_dirs, extra_keypair, collect_email, monkeypatch):


#     filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"

#     settings['work_dir'] = test_dirs['work']
#     settings['keys_dir'] = test_dirs['keys']
#     settings['mode']  = 'decrypt'
#     settings['scan_pipes']  = [
#         {"name": "dummy filter", "cmd": filter_command}
#     ]

#     # We bypass the stdin read and retrieve manually the message
#     def mail_getter(msg):
#         msg['inmail'] = collect_email
#         return msg

#     monkeypatch.setattr(pEpgate, "get_message", mail_getter)

#     pEpgate.main([])



# @pytest.mark.parametrize('collect_email', ["basic_filter_evil.enc.eml"], indirect=True)
# def test_filter_enc_evil(settings, test_dirs, extra_keypair, collect_email, monkeypatch):


#     filter_command = f"python {test_dirs['root'] / 'dummy_filter.py'}"

#     settings['work_dir'] = test_dirs['work']
#     settings['keys_dir'] = test_dirs['keys']
#     settings['mode']  = 'decrypt'
#     settings['scan_pipes']  = [
#         {"name": "dummy filter", "cmd": filter_command}
#     ]

#     # We bypass the stdin read and retrieve manually the message
#     def mail_getter(msg):
#         msg['inmail'] = collect_email
#         return msg

#     monkeypatch.setattr(pEpgate, "get_message", mail_getter)

#     with pytest.raises(SystemExit) as exec_info:
#         pEpgate.main([])
#     assert exec_info.type == SystemExit
#     assert exec_info.value.code == 1
