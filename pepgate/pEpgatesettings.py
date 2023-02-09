import os
from datetime    import datetime

settings = {}

def init_settings(filesettings):
    """
    Init settings dict with data from the settings.toml file
    """
    global settings
    # Postfix sets this to "C" by default, we want full Unicode support though
    os.environ['LANG'] = os.environ['LC_ALL'] = "en_US.UTF-8"
    home               = os.getcwd()

    for setting, value in filesettings.items():
        settings[setting] = value

    settings['gate_version']       = "2.12"
    settings['locktimeout']        = 60
    settings['lastactiontime']     = datetime.now()
    settings['adminlog']           = ""
    settings['textlog']            = ""
    settings['htmllog']            = ""
    settings['logpath']            = None
    settings['dts']                = None
    settings['home']               = home
    # settings['workdirpath']        = os.path.join(home, settings['work_dir'])
    # settings['keypath']            = os.path.join(home, settings['keys_dir'])
    # settings['logfilepath']        = os.path.join(home, settings['logfile'])
    # settings['fwdmappath']         = os.path.join(home, settings['forwarding_map'])
    # settings['usermappath']        = os.path.join(home, settings['username_map'])
    # settings['nextmxpath']         = os.path.join(home, settings['nextmx_map'])
    # settings['aliasespath']        = os.path.join(home, settings['aliases_map'])
    settings['lockfilepath']       = os.path.join(home, "pEpGate.lock")
    settings['inmail']             = ""
