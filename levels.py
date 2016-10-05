import sys
import json
import os
from pprint import pprint
from StringIO import StringIO

import pygame

import phys_objects
import paths
import gamestate
import equations
import options
from utilities import Utils
import level_loader

# Level class is essentially just a list of the entities in a level, as well as information 
# about the level including its name and number.
class Level:
        def __init__(self, name, entity_list, spawn_list, theme_dict):
            self.name = name
            self.num = -1
            self.entity_list = entity_list[:]
            self.spawn_list = spawn_list[:]
            self.theme_lookup = dict(theme_dict)

            self.actor = self._find_player()
            if self.actor == None:
                print "levels.Level: Warning: No actor found in loaded level!"
            
        def add_object(self, obj):
            self.entity_list.append(obj)
            
        def remove_object(self, obj):
            self.entity_list.remove(obj)
            
        def get_objects_at(self, (x, y)):
            return [obj for obj in self.entity_list if obj.rect.collidepoint(x,y)]
            
        def bring_out_yer_dead(self):
            self.entity_list = filter(lambda x : not (hasattr(x, "is_alive") and not x.is_alive) or x is self.actor, self.entity_list)
            
        def _find_player(self):
            for elem in self.entity_list:
                if elem.is_actor() and elem.is_player:
                    return elem
            return None
            
        def set_actor(self, new_actor):
            new_actor.reset()
            if self.actor != None:
                new_actor.set_xy(self.actor.x(), self.actor.y()) 
            self.entity_list.remove(self.actor)
            self.entity_list.append(new_actor)
            self.actor = new_actor
        
        
        def to_json(self):
            my_json = {
                "info": {
                    "name":self.name,
                    "version":"1.1"
                },
                "blocks": [],
                "spawns":[],
                "themes":{}
            }
            
            for entity in self.entity_list:
                if entity.is_block():
                    my_json["blocks"].append(entity.to_json())
            for spawn in self.spawn_list:
                my_json["spawns"].append(spawn.to_json())
            for id in self.theme_lookup:
                theme = self.theme_lookup[id]
                if theme.is_built_in:
                    my_json["themes"][id] = theme.built_in_id
                else:
                    my_json["themes"][id] = theme.to_json()
                    
            return my_json
            
BUILT_IN_THEMES = {}
                
class Theme:
    DEFAULT_VALUES = {
        "normal_color":[128, 128, 128],
        "normal_perturb":20,
        "perturb_grayscale_only":True,
        "moving_color":[128, 128, 128],
        "moving_perturb":0,
        "bad_color":[255, 0, 0],
        "background_color":[0, 0, 0],
        "finish_color":[0, 255, 0]
    }
    
    def __init__(self, **kwargs):
        self.is_built_in = False
        
        self.values = dict(Theme.DEFAULT_VALUES)
        for key in kwargs:
            if not key in self.values:
                raise ValueError("Theme param not recognized: "+str(key))
            else:
                self.values[key] = kwargs[key]
    
    def apply(self, object):
        if object.is_moving_block():
            object.set_color(self.values["moving_color"], self.values["moving_perturb"], self.values["perturb_grayscale_only"])
        elif object.is_bad_block():
            object.set_color(self.values["bad_color"], 0)
        elif object.is_finish_block():
            object.set_color(self.values["finish_color"], 0)
        elif object.is_block():
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
        
    def to_json(self):
        if self.id != None:
            return self.id
        else:
            return self.values
    
    @staticmethod
    def from_json(data):
        if isinstance(data, basestring):
            return BUILT_IN_THEMES[data]
        else:
            result = Theme()
            for key in data:
                if not key in result.values:
                    raise ValueError("Theme param not recognized: "+str(key))
                else:
                    result.values[key] = data[key]
            
            return result
            
    def build_in(self, id):
        self.is_built_in = True
        self.built_in_id = id
        return self

BUILT_IN_THEMES.update({
    "default":Theme().build_in("default"),
    "ice":Theme(
        normal_color=[145, 200, 220], 
        perturb_grayscale_only=False, 
        background_color=[30, 60, 70]).build_in("ice"),
    "fire":Theme(
        normal_color=[170, 90, 90], 
        perturb_grayscale_only=False, 
        background_color=[95, 5, 5]).build_in("fire"),
    "forest":Theme(
        normal_color=[80, 165, 60], 
        perturb_grayscale_only=False, 
        background_color=[11, 30, 6]).build_in("forest"),
    "snow":Theme(
        normal_color=[200, 200, 200], 
        perturb_grayscale_only=True, 
        background_color=[50, 50, 50]).build_in("snow"),
    "rainbow":Theme(
        normal_color=[128, 128, 128], 
        perturb_grayscale_only=False, 
        normal_perturb=128, 
        background_color=[0, 0, 0], 
        moving_color=[128, 128, 128], 
        moving_perturb=128).build_in("rainbow")
})
       
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
        self.ghosts = [phys_objects.Ghost.from_json(g) for g in highscores["ghosts"]]
        
    def get_num_levels(self):
        return len(self.level_filenames)
        
    def get_best_level_time(self, level_num):
        return self.best_individual_scores[level_num]
    
    def get_best_run_time(self):
        return self.best_overall_run_total
        
    def load_level(self, num, actor, reset_ghost=True):
        level = level_loader.load(self.file_dir + "/" + self.level_filenames[num])
        if level == None:
            print "Level "+str(num)+" failed to load, using Void Level instead."
            level = self.create_void_level()
        
        self.level_num = num
        level.set_actor(actor)
        
        if self.ghosts[num] != None:
            if reset_ghost:
                self.ghosts[num].reset()
            level.add_object(self.ghosts[num])
            
        self.current_level = level
        
    def update_level_highscore(self, level_num, time, ghost_recorder=None):
        dirty = False
    
        current_record = self.best_individual_scores[level_num]
        if current_record == None or time < current_record:
            print "***NEW LEVEL RECORD***"
            print "Level "+str(level_num)+"'s record of "+str(Utils.format_time(current_record))+" broken with "+gamestate.Utils.format_time(time)+"!"
            self.best_individual_scores[level_num] = time
            if ghost_recorder != None:
                self.ghosts[level_num] = ghost_recorder.to_ghost()
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
        highscores["ghosts"] = [phys_objects.Ghost.to_json(g) for g in self.ghosts]
        
        file = open(self.get_highscores_filename(), 'w')
        
        if suppress_printing > 1:
            print "dumping: "
            print json.dumps(highscores, indent=4, sort_keys=True)
        
        json_string = json.dumps(highscores, indent=4, sort_keys=True)
        json_string = Utils.make_json_pretty(json_string)
        file.write(json_string)
        
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
            json_str = json.dumps(hs_dict, indent=4, sort_keys=True)
            json_str = Utils.make_json_pretty(json_str)
            #json.dump(hs_dict, file, indent=4, sort_keys=True)
            file.write(json_str)
            
            file.close()
        return hs_dict
        
    @staticmethod
    def generate_empty_highscores_dict(num_levels):
        return {
                "best_overall_run_total":None,
                "best_overall_run_scores":[None for i in range(0,num_levels)],
                "best_individual_scores":[None for i in range(0,num_levels)],
                "ghosts":[None for i in range(0, num_levels)]
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
        

        
        
