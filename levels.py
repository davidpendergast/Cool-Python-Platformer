import sys
import json
import os
from pprint import pprint
from StringIO import StringIO

import pygame

import phys_objects
import gamestate
import new_equation
import options
from utilities import Utils

# Level class is essentially just a list of the entities in a level, as well as information 
# about the level including its name and number.
class Level:
        def __init__(self, entity_list, name, theme=None):
            if theme == None:
                theme = Theme()
            self.name = name
            self.num = -1
            
            self.entity_list = entity_list[:]
            self.background_color = theme
            for obj in self.entity_list:
                theme.apply(obj)

            self.actor = self._find_player()
            if self.actor == None:
                print "levels.Level: Warning: No actor found in loaded level!"
            
        def add_object(self, obj):
            self.entity_list.append(obj)
            
        def remove_object(self, obj):
            self.entity_list.remove(obj)
            
        def _find_player(self):
            for elem in self.entity_list:
                if isinstance(elem, phys_objects.Actor) and elem.is_player:
                    return elem
            return None
            
        def set_actor(self, new_actor):
            new_actor.reset()
            if self.actor != None:
                new_actor.set_xy(self.actor.x(), self.actor.y()) 
            self.entity_list.remove(self.actor)
            self.entity_list.append(new_actor)
            self.actor = new_actor
 
class Theme:
    def __init__(self, id=None):
        if id == None:
            self.values = {
                "normal_color":(128, 128, 128),
                "normal_perturb":20,
                "perturb_grayscale_only":True,
                "moving_color":(128, 128, 128),
                "moving_perturb":0,
                "bad_color":(255, 0, 0),
                "background_color":(0, 0, 0),
                "finish_color":(0, 255, 0)
            }
        else:
            global BUILT_IN_THEMES
            if id in BUILT_IN_THEMES:
            
                self.values = BUILT_IN_THEMES[id].values
            else:
                raise ValueError("Invalid theme id: "+str(id))
    
    def apply(self, object):
        if isinstance(object, phys_objects.MovingBlock):
            object.set_color(self.values["moving_color"], self.values["moving_perturb"], self.values["perturb_grayscale_only"])
        elif isinstance(object, phys_objects.BadBlock):
            object.set_color(self.values["bad_color"], 0)
        elif isinstance(object, phys_objects.FinishBlock):
            object.set_color(self.values["finish_color"], 0)
        elif isinstance(object, phys_objects.Block):
            object.set_color(self.values["normal_color"], self.values["normal_perturb"], self.values["perturb_grayscale_only"])
    
    def __eq__(self, other):
        if not isinstance(other, Theme):
            return False
        return self.normal_color == other.normal_color and \
            self.normal_perturb == other.normal_perturb and \
            self.perturb_grayscale_only == other.perturb_grayscale_only and \
            self.moving_color == other.moving_color and \
            self.moving_perturb == other.moving_perturb and \
            self.bad_color == other.bad_color and \
            self.background_color == other.background_color and \
            self.finish_color == other.finish_color
    
    def set(self, field, value):
        if field not in self.values:
            raise ValueError("Theme field not recognized: "+str(field))
        self.values[field] = value
        return self

BUILT_IN_THEMES = {
    "ice":Theme().set("normal_color", (145, 200, 220)).set("perturb_grayscale_only", False).set("background_color", (30, 60, 70)),
    "fire":Theme().set("normal_color", (170, 90, 90)).set("perturb_grayscale_only", False).set("background_color", (95, 5, 5)),
    "rainbow":Theme().set("normal_color", (128, 128, 128)).set("perturb_grayscale_only", False).set("normal_perturb", 128).set("background_color", (0, 0, 0)).set("moving_color", (128, 128, 128)).set("moving_perturb", 128)
}
       
class LevelManager:
    def __init__(self, settings):
        self.settings = settings
        self.level_num = 0
        self.current_level = None
        
        self.file_dir = settings.level_path()    # "levels/something", most likely
        self.level_filenames = self.read_filenames_from_header()
        highscores = self.load_or_create_highscore_data()  
        self.current_run_times = [None for i in range(0,self.get_num_levels())]
        
        self.best_overall_run_total = Utils.unformat_time(highscores["best_overall_run_total"])
        self.best_individual_scores = [Utils.unformat_time(highscores["best_individual_scores"][i]) for i in range(self.get_num_levels())]
        self.best_overall_run_scores = [Utils.unformat_time(highscores["best_overall_run_scores"][i]) for i in range(self.get_num_levels())]
        
    def get_num_levels(self):
        return len(self.level_filenames)
        
    def load_level(self, num, actor):
        level = LevelReader.load(self.file_dir + "/" + self.level_filenames[num])
        if level == None:
            print "Level "+str(num)+" failed to load, using Void Level instead."
            level = self.create_void_level()
        
        self.level_num = num
        level.set_actor(actor)
        self.current_level = level
        
    def update_level_highscore(self, level_num, time):
        dirty = False
    
        current_record = self.best_individual_scores[level_num]
        if current_record == None or time < current_record:
            print "***NEW LEVEL RECORD***"
            print "Level "+str(level_num)+"'s record of "+str(Utils.format_time(current_record))+" broken with "+gamestate.Utils.format_time(time)+"!"
            self.best_individual_scores[level_num] = time
            dirty = True
        else:
            print "Level "+str(level_num)+" completed! Time: " +str(Utils.format_time(time))+"\t Best: "+gamestate.Utils.format_time(current_record)
            
        self.current_run_times[level_num] = time
        if level_num == self.get_num_levels()-1: #last level
            final_time = 0
            for val in self.current_run_times:
                if val == None:
                    final_time = None
                    break;
                else:
                    final_time += val
            
            if final_time != None:
                if self.best_overall_run_total == None or final_time < self.best_overall_run_total:
                    print "***NEW FULL RUN RECORD***"
                    print "Previous record "+str(Utils.format_time(self.best_overall_run_total))+" broken with "+str(Utils.format_time(final_time))
                    self.best_overall_run_total = final_time
                    self.best_overall_run_scores = [self.current_run_times[i] for i in range(0,self.get_num_levels())]
                    dirty = True
                else:
                    print "Game Completed! Final time: "+str(Utils.format_time(final_time))
        
        if dirty:
            self.dump_highscores_to_file(0)
        
    def dump_highscores_to_file(self, suppress_printing=0):
        "0 = print nothing, 1 = print message, 2 = print entire file"
        if self.settings.dev_mode():
            print "Not saving high scores because we're in dev mode"
            return
        
        if suppress_printing > 0:
            print "Saving highscores to "+self.get_highscores_filename()+"..."
        highscores = LevelManager.generate_empty_highscores_dict(self.get_num_levels())
        highscores["best_overall_run_total"] = Utils.format_time(self.best_overall_run_total)
        highscores["best_individual_scores"] = [Utils.format_time(self.best_individual_scores[i]) for i in range(0, self.get_num_levels())]
        highscores["best_overall_run_scores"] = [Utils.format_time(self.best_overall_run_scores[i]) for i in range(0, self.get_num_levels())]
        
        file = open(self.get_highscores_filename(), 'w')
        
        if suppress_printing > 1:
            print "dumping: "
            print json.dumps(highscores, indent=4, sort_keys=True)
        
        json.dump(highscores, file, indent=4, sort_keys=True)
        
        file.close()
        
    def create_void_level(self):
        entity_list = []
       
        entity_list.append(phys_objects.Block(128, 128).set_xy(0, 128))
        entity_list.append(phys_objects.FinishBlock(16, 16).set_xy(56, -64))
        
        actor = phys_objects.Actor().set_xy(32, 96)
        actor.is_player = True
        entity_list.append(actor)
        
        return Level(entity_list, "The Void")
        
    def read_filenames_from_header(self):
        res = []
        print "Reading " + self.file_dir + "/header.txt..."
        header = open(self.file_dir + "/header.txt")
        for line in header:
            if line[-1] == '\r':
                line = line[:len(line)-1]
            if line[-1] == '\n':
                line = line[:len(line)-1]
                
            res.append(line)
        
        print "\tlevel filenames are:"
        for filename in res:
            print "\t\t"+str(filename)
            
        return res
        
    def load_or_create_highscore_data(self):
        hs_dict = None
        if os.path.isfile("./"+self.get_highscores_filename()) and os.path.getsize("./"+self.get_highscores_filename()) > 0:
            print "Reading "+self.file_dir+"/highscores.json..."
            with open(self.file_dir+"/highscores.json") as data_file:
                hs_dict = json.load(data_file)
                hs_dict = self.repair_highscore_data_if_necessary(hs_dict)
        else:
            print "Creating " + self.file_dir+"/highscores.json..."
            num_levels = self.get_num_levels()
            hs_dict = LevelManager.generate_empty_highscores_dict(self.get_num_levels())
            
            file = open(self.file_dir+"/highscores.json", 'w')
            
            print "dumping: "
            print json.dumps(hs_dict, indent=4, sort_keys=True)
            
            json.dump(hs_dict, file, indent=4, sort_keys=True)
            
            file.close()
        return hs_dict
        
    @staticmethod
    def generate_empty_highscores_dict(num_levels):
        return {
                "best_overall_run_total":None,
                "best_overall_run_scores":[None for i in range(0,num_levels)],
                "best_individual_scores":[None for i in range(0,num_levels)]
            }
    
    def repair_highscore_data_if_necessary(self, highscore_data):
        damaged = len(highscore_data["best_individual_scores"]) != self.get_num_levels()
        damaged |= len(highscore_data["best_overall_run_scores"]) != self.get_num_levels()
        
        if damaged:
            print "highscores.json is invalid, wiping scores." # a bit excessive but w/ever
            return self.generate_empty_highscores_dict(self.get_num_levels())
            
        return highscore_data    
        
    def get_highscores_filename(self):
        return self.file_dir+"/highscores.json"
        
class LevelReader:
    @staticmethod
    def load(filename):
        entity_list = []
        
        try:
            with open(filename) as json_file:
                data = json.load(json_file)
            
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
                            x_path = new_equation.pythonify(str(elem["x_path"]))
                            y_path = new_equation.pythonify(str(elem["y_path"]))
                            path = phys_objects.Path(x_path, y_path)
                        elif "x_points" in elem and "y_points" in elem and "speed" in elem:
                            x_points = elem["x_points"]
                            y_points = elem["y_points"]
                            speed = elem["speed"]
                            path = phys_objects.PointPath(x_points, y_points, speed)
                        
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
            
            theme = None 
            if "theme" in data:
                elem = data["theme"]
                if isinstance(elem, type({})):
                    theme = Theme()
                    for key in elem:
                        val = elem[key]
                        if isinstance(val, list):
                            val = tuple(val)
                        theme.set(key, val)
                else:
                    # elem = "ice", "fire", ...
                    theme = Theme(elem)
                    
            
            actor = phys_objects.Actor().set_xy(int(data["actor"]["x"]), int(data["actor"]["y"]))
            actor.is_player = True
            
            entity_list.append(actor)
            entity_list = sorted(entity_list)
            
            return Level(entity_list, name, theme)
        except:
            print "Error while loading "+filename+":"
            for err in sys.exc_info():
                print "\t"+str(err)
                
        return None
        
        
