
import os
import json

def override_settings(tmp_dir, new_params):

    settings_file = os.path.join(tmp_dir, 'settings_tests.json')
    json_settings = {}


    with open(settings_file, "r") as file:
        filesettings = json.load(file)
    
    for setting, value in filesettings.items():
        json_settings[setting] = value


    os.remove(settings_file)
        
    
    json_settings.update(new_params)

    json_object = json.dumps(json_settings, indent=4)
    
    with open(settings_file, "w") as outfile:
        outfile.write(json_object)