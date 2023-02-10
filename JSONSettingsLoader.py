import json

settings_file = open('settings.map')
settings_bulk = json.load(settings_file)
settings_file.close()

settings = {}
scan_pipes = []

for (setting, value) in settings_bulk.items():
    settings[setting] = value


for item in (settings['scan_pipes']):
    print(item['name'])
    print(item['cmd'])
