import sys
import json
import traceback

import blocks, actors
import paths
import levels

# filled at bottom of file
LOADERS = {}

def load(filename):
    try:
        with open(filename) as json_file:
            data = json.load(json_file)
        
            version_num = data["info"]["version"]
            data["filename"] = filename
            if version_num in LOADERS:
                return LOADERS[version_num](data)
            else:
                raise ValueError("Unsupported version number: "+str(version_num))
    except:
        print(f'Error while loading {filename}:')
        traceback.print_exc()
        return None

def _load_version_1_1(data):
    _validate_version_1_1(data)
    
    name = data["info"]["name"]
    filename = data["filename"]
    theme_lookup = dict(levels.BUILT_IN_THEMES)
    spawns_list = []
    entity_list = []
    
    for theme_id in data["themes"]:
        theme_val = data["themes"][theme_id]
        new_theme = levels.Theme.from_json(theme_val)
        theme_lookup[theme_id] = new_theme
    for elem in data["blocks"]:
        new_block = blocks.BlockFactory.from_json(elem)
        entity_list.append(new_block)
    for elem in data["spawns"]:
        new_spawn = actors.SpawnPoint.from_json(elem)
        spawns_list.append(new_spawn)
    
    return levels.Level(name, entity_list, spawns_list, theme_lookup, filename)
        
def _validate_version_1_1(data):
    error_msg = ""
    for section in ("info", "spawns", "blocks", "themes"):
        if not section in data:
            error_msg += "\nmissing section: "+section
            
    # todo - more stuff   
    # player spawn
    # default theme
            
    if error_msg != "":
        raise ValueError(error_msg[1:]) # rem leading '\n'

LOADERS["1.1"] = _load_version_1_1
