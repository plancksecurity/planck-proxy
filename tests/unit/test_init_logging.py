import os
import codecs

def test_init_logging_creates_log_file(set_settings, test_dirs):
    settings = set_settings
    settings["mode"] = "decrypt"
    settings["work_dir"] = str(test_dirs["work"])

    from proxy.utils.message import Message
    message = Message()
    message.msgfrom = "user@example.com"
    message.inmail = "This is a test message."

    from proxy.utils.logging import init_logging
    init_logging(message)

    logpath = settings["logpath"]
    assert os.path.exists(logpath)

    logfilename = os.path.join(logpath, "in." + settings["mode"] + ".original.eml")
    assert os.path.exists(logfilename)

    with codecs.open(logfilename, "r", "utf-8") as logfile:
        contents = logfile.read()
        assert contents == "This is a test message."
