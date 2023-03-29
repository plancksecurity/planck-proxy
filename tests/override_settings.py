
import os
import json


def override_settings(settings_file, new_params):
    """
    This method updates the settings of a JSON file with new parameters.

    Args:
        settings_file (str): The path to the JSON file containing the current settings.
        new_params (dict): The new parameters to be added or updated in the settings.

    Returns:
        None
    """
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
