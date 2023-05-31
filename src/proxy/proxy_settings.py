import os
import json

from pathlib import Path
from datetime import datetime

settings = {
    "logfile": "debug.log",
    "work_dir": "work",
    "keys_dir": "keys",
}


def init_settings(settings_file=None):
    """
    Init settings dict with data from the settings.json file

    Returns:
        None
    """
    global settings
    # Postfix sets this to "C" by default, we want full Unicode support though
    os.environ["LANG"] = os.environ["LC_ALL"] = "en_US.UTF-8"
    home = os.getcwd()

    if settings_file:
        settings_path = settings_file
    else:
        # Add data from the Json file to the settings dict
        settings_path = os.path.join(home, "settings.json")

    if not os.path.isfile(settings_path):
        print(
            f"No settings found at {settings_path}, please set all the settings into environment"
            "variables or create a settings.json file."
        )
    else:
        with open(settings_path, "rb") as f:
            filesettings = json.load(f)

        print(f"rewrite settings with {settings_path}")
        for setting, value in filesettings.items():
            settings[setting] = value

    settings["home"] = home
    settings["locktimeout"] = 60
    settings["lastactiontime"] = datetime.now()
    settings["adminlog"] = ""
    settings["textlog"] = ""
    settings["htmllog"] = ""
    settings["logpath"] = None
    settings["dts"] = None
    settings["lockfilepath"] = os.path.join(home, "proxy.lock")
    settings["logfile"] = os.path.join(home, settings["logfile"])

    return settings
