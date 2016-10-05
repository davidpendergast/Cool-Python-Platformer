import sys
import json

import phys_objects
import paths
import equations
import levels
from utilities import Utils

# filled at bottom of file
LOADERS = {}

def load(filename):
    #try:
        with open(filename) as json_file:
            data = json.load(json_file)
        
            version_num = data["info"]["version"]
            if version_num in LOADERS:
                return LOADERS[version_num](data)
            else:
                raise ValueError("Unknown version number: "+str(version_num))
    #except:
    #    print "Error while loading "+filename+":"
    #   for err in sys.exc_info():
    #       print "\t"+str(err)

def _load_1_1(data):
    _validate_1_1(data)
    
    name = data["info"]["name"]
    theme_lookup = dict(levels.BUILT_IN_THEMES)
    spawns_list = []
    entity_list = []
    
    for theme_id in data["themes"]:
        theme_val = data["themes"][theme_id]
        new_theme = levels.Theme.from_json(theme_val)
        theme_lookup[theme_id] = new_theme
    for elem in data["blocks"]:
        new_block = phys_objects.BlockFactory.from_json(elem)
        entity_list.append(new_block)
    for elem in data["spawns"]:
        new_spawn = phys_objects.SpawnPoint.from_json(elem)
        spawns_list.append(new_spawn)
        entity_list.append(new_spawn.get_actor())
        
    for spawner in spawns_list:
        spawner.do_spawn()
    
    for entity in entity_list:
        theme_id = entity.get_theme_id()
        theme = theme_lookup[theme_id]
        if theme != None:
            theme.apply(entity)
        else:
            raise ValueError("Unrecognized theme: "+str(theme_id))
        
    return levels.Level(name, entity_list, spawns_list, theme_lookup)
        
        
def _validate_1_1(data):
    error_msg = ""
    for section in ("info", "spawns", "blocks", "themes"):
        if not section in data:
            error_msg += "\nmissing section: "+section
            
    # todo - more stuff   
    # player spawn
    # default theme
            
    if error_msg != "":
        raise ValueError(error_msg[1:]) # rem leading '\n'
        
        
def _load_1_0(data):
    entity_list = []
    name = "<Unnamed>"
    if "info" in data and "name" in data["info"]:
        name = data["info"]["name"]
    
    if "blocks" in data:
        for elem in data["blocks"]:
            if elem["type"] == "normal":
                block = phys_objects.Block(int(elem["width"]), int(elem["height"]))
                block.set_xy(int(elem["x"]), int(elem["y"]))
            elif elem["type"] == "bad":
                block = phys_objects.BadBlock(int(elem["width"]), int(elem["height"]))
                block.set_xy(int(elem["x"]), int(elem["y"]))
            elif elem["type"] == "finish":
                block = phys_objects.FinishBlock(int(elem["width"]), int(elem["height"]))
                block.set_xy(int(elem["x"]), int(elem["y"]))
            elif elem["type"] == "moving":
                path = None
                if "x_path" in elem and "y_path" in elem:
                    x_path = equations.pythonify(str(elem["x_path"]))
                    y_path = equations.pythonify(str(elem["y_path"]))
                    path = paths.Path(x_path, y_path)
                elif "x_points" in elem and "y_points" in elem and "speed" in elem:
                    x_points = elem["x_points"]
                    y_points = elem["y_points"]
                    speed = elem["speed"]
                    path = paths.PointPath(x_points, y_points, speed)
                
                block = phys_objects.MovingBlock(int(elem["width"]), int(elem["height"]), path)
            else:
                continue
            entity_list.append(block)
    else:
        print "no blocks data in "+filename+"?"
        
    if "enemies" in data:
        for elem in data["enemies"]:
            if elem["type"] == "smart":
                enemy = phys_objects.Enemy.get_smart_walker_enemy(int(elem["x"]), int(elem["y"]))
            elif elem["type"] == "dumb":
                enemy = phys_objects.Enemy.get_stupid_walker_enemy(int(elem["x"]), int(elem["y"]))
            elif elem["type"] == "bad":
                enemy = phys_objects.Enemy.get_bad_enemy(int(elem["x"]), int(elem["y"]))
            else:
                continue
            entity_list.append(enemy)
    
    if "spawns" in data:
        pass
        
    theme = None 
    if "theme" in data:
        elem = data["theme"]
        if isinstance(elem, type({})):
            theme = Theme()
            for key in elem:
                val = elem[key]
                theme.set(key, val)
        else:
            # elem = "ice", "fire", ...
            theme = levels.Theme(elem)
            
    
    actor = phys_objects.Actor().set_xy(int(data["actor"]["x"]), int(data["actor"]["y"]))
    actor.is_player = True
    
    entity_list.append(actor)
    entity_list = sorted(entity_list)
    
    return levels.Level(entity_list, name, theme)

LOADERS["1.0"] = _load_1_0
LOADERS["1.1"] = _load_1_1

if __name__ == "__main__":
    filename = "levels/v2_levels/test_level.json"
    level = load(filename)
