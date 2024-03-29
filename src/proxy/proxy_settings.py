import os
import json

from pathlib import Path
from datetime import datetime, timezone

settings = {
    "work_dir": "work",
    "keys_dir": "keys",
    "export_dir": "export",
    "export_log_level": "DEBUG",
    "home": "",
    "recipient": False,
}


def init_settings(settings_file=None):
    """
    Init settings dict with data from the settings.json file. Creates the HOME folder if it does not exist

    Returns:
        None
    """
    global settings
    # Postfix sets this to "C" by default, we want full Unicode support though
    os.environ["LANG"] = os.environ["LC_ALL"] = "en_US.UTF-8"

    if settings_file is not None:
        with open(settings_file, "rb") as f:
            filesettings = json.load(f)

        print(f"rewrite settings with {settings_file}")
        for setting, value in filesettings.items():
            settings[setting] = value

    if settings["home"] == "":
        settings["home"] = os.getcwd()
    else:
        if not os.path.exists(settings["home"]):
            os.makedirs(settings["home"])

    settings["locktimeout"] = 60
    settings["lastactiontime"] = datetime.now(timezone.utc)
    settings["adminlog"] = ""
    settings["textlog"] = ""
    settings["htmllog"] = ""
    settings["logpath"] = None
    settings["exportpath"] = None
    settings["dts"] = None
    settings["lockfilepath"] = os.path.join(settings["home"], "proxy.lock")
    settings["project_root"] = Path(os.path.dirname(__file__))

    if os.name == "posix":
        database_folder = ".pEp"
    else:
        database_folder = "pEp"

    settings["database_folder"] = database_folder

    return settings
