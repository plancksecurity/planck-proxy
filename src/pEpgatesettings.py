import os
import json

from pathlib     import Path
from datetime    import datetime

settings = {}

def init_settings():
    """
    Init settings dict with data from the settings.toml file
    """
    global settings
    # Postfix sets this to "C" by default, we want full Unicode support though
    os.environ['LANG'] = os.environ['LC_ALL'] = "en_US.UTF-8"
    home               = str(Path(os.path.dirname(__file__)).parent)

    # Add data from the toml file to the settings dict
    settings_path = os.path.join(home, "settings.json")
    if not os.path.isfile(settings_path):
        print(f"No settings found at {settings_path}, please set all the settings into environment" \
        "variables or create a settings.json file.")
    else:
        with open(settings_path, "rb") as f:
            filesettings = json.load(f)

        for setting, value in filesettings.items():
            settings[setting] = value

    settings['home']               = home
    settings['locktimeout']        = 60
    settings['gate_version']       = "2.12"
    settings['lastactiontime']     = datetime.now()
    settings['adminlog']           = ""
    settings['textlog']            = ""
    settings['htmllog']            = ""
    settings['logpath']            = None
    settings['dts']                = None
    settings['lockfilepath']       = os.path.join(home, "pEpGate.lock")
    settings['logfile']            = os.path.join(home, settings['logfile'])
