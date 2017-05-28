import sys
import json
import os

import pygame

import blocks, actors
import paths
import gamestate
import options
import utilities
import level_loader

class Level:
    def __init__(self, name, entity_list, spawn_list, theme_dict, filename):
        self.name = name
        self.num = -1
        self.entity_list = entity_list[:]
        self._entity_list_dirty = True # List needs sorting
        self.spawn_list = spawn_list[:]
        self.theme_lookup = dict(theme_dict)
        self.background_color = self.theme_lookup["default"].values["background_color"]
        self.filename = filename
        
        for spawner in spawn_list:
            self.entity_list.append(spawner.get_actor())
            spawner.do_spawn()
            
        for entity in self.entity_list:
            theme_id = entity.get_theme_id()
            if theme_id in self.theme_lookup:
                self.theme_lookup[theme_id].apply(entity)
            else:
                utilities.log("WARN: Unrecognized theme id: "+str(theme_id))
                self.theme_lookup["default"].apply(entity)
        
        self.actor = self._find_player()
        if self.actor == None:
            utilities.log("levels.Level: Warning: No actor found in loaded level!")
        self.sort_if_dirty()
    
    def _sort_entities(self):
        sorter = lambda x,y: x.get_update_priority() - y.get_update_priority()
        self.entity_list.sort(cmp=sorter)
        self._entity_list_dirty = False
    
    def add_object(self, obj, sort_now=True):
        self.entity_list.append(obj)
        if sort_now:
            self._sort_entities()
        else:
            self._entity_list_dirty = True
        
    def sort_if_dirty(self):
        if self._entity_list_dirty:
            self._sort_entities()
        
    def remove_object(self, obj):
        index = self.entity_list.index(obj)
        del self.entity_list[index]
        
    def get_objects_at(self, (x, y)):
        return [obj for obj in self.entity_list if obj.rect.collidepoint(x,y)]
        
    def bring_out_yer_dead(self):
        """Removes all dead non-player Boxes from the level. 
           Returns the list of removed items (and the player if the player
           is dead). """
        dead = filter(lambda x : not x.alive() and x is not self.actor, self.entity_list)
        
        if len(dead) > 0:
            self.entity_list = [x for x in self.entity_list if x not in dead]
            
        if self.actor != None and not self.actor.is_alive:
            dead.append(self.actor)
        
        return dead
        
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
            theme_json = theme.to_json()
            
            # want to avoid redundant entries like "ice":"ice"
            if theme_json != id:
                my_json["themes"][id] = theme_json

        return my_json
            
BUILT_IN_THEMES = {}
                
class Theme:
    DEFAULT_VALUES = {
        "normal_color":[128, 128, 128],
        "normal_perturb":20,
        "moving_color":[128, 128, 128],
        "moving_perturb":0,
        "bad_color":[255, 0, 0],
        "bad_perturb":0,
        "finish_color":[0, 255, 0],
        "finish_perturb":0,
        "background_color":[0, 0, 0],
        "perturb_grayscale_only":True
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
        if object.is_bad_block():
            object.set_color(
                    self.values["bad_color"],
                    self.values["bad_perturb"],
                    self.values["perturb_grayscale_only"])
        elif object.is_finish_block():
            object.set_color(
                    self.values["finish_color"],
                    self.values["finish_perturb"],
                    self.values["perturb_grayscale_only"])
        elif object.is_moving_block():
            object.set_color(
                    self.values["moving_color"], 
                    self.values["moving_perturb"], 
                    self.values["perturb_grayscale_only"])
        elif object.is_block():
            object.set_color(
                    self.values["normal_color"], 
                    self.values["normal_perturb"], 
                    self.values["perturb_grayscale_only"])
        
    def to_json(self):
        if self.is_built_in:
            return self.built_in_id
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
        background_color=[15, 30, 35]).build_in("ice"),
    "fire":Theme(
        normal_color=[170, 90, 90], 
        bad_perturb=10,
        perturb_grayscale_only=False, 
        background_color=[20, 5, 5]).build_in("fire"),
    "forest":Theme(
        normal_color=[80, 165, 60], 
        perturb_grayscale_only=False, 
        background_color=[5, 15, 6]).build_in("forest"),
    "snow":Theme(
        normal_color=[200, 200, 200], 
        perturb_grayscale_only=True, 
        background_color=[25, 25, 25]).build_in("snow"),
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
        
        self.file_dir = settings.level_path()
        self.level_filenames = self.read_filenames_from_header()
        highscores = self.load_or_create_highscore_data()  
        self.current_run_times = [None for i in range(0,self.get_num_levels())]
        
        self.best_overall_run_total = utilities.unformat_time(highscores["best_overall_run_total"])
        self.best_individual_scores = [utilities.unformat_time(highscores["best_individual_scores"][i]) for i in range(self.get_num_levels())]
        self.best_overall_run_scores = [utilities.unformat_time(highscores["best_overall_run_scores"][i]) for i in range(self.get_num_levels())]
        self.ghosts = [actors.Ghost.from_json(g) for g in highscores["ghosts"]]
        
    def get_checksum(self, level_num):
        with open(self.get_filepath(level_num)) as level_file:
            text = level_file.read()
            bigprime = 8002823
            checksum = 1
            
            for i in range(0, len(text)):
                char = text[i]
                checksum += (ord(char) * i)
                checksum = checksum % bigprime
                
            return checksum
        return -1
    
    def get_num_levels(self):
        return len(self.level_filenames)
        
    def get_best_level_time(self, level_num):
        return self.best_individual_scores[level_num]
    
    def get_best_run_time(self):
        return self.best_overall_run_total
        
    def load_level(self, num, actor=None, reset_ghost=True):
        loaded_successfully = True
        level = level_loader.load(self.get_filepath(num))
        if level == None:
            utilities.log("Level "+str(num+1)+" failed to load, using Void Level instead.")
            level = self.create_void_level()
            loaded_successfully = False
        
        self.level_num = num
        level.num = num
        if actor is not None:
            level.set_actor(actor)
        
        if self.ghosts[num] != None and not self.settings.edit_mode():
            if reset_ghost:
                self.ghosts[num].reset()
            level.add_object(self.ghosts[num])
        
        self.current_level = level
        return loaded_successfully
        
    def get_filepath(self, level_num):
        return self.file_dir + "/" + self.level_filenames[level_num]
        
    def update_level_highscore(self, level_num, time, ghost_recorder=None):
        dirty = False
    
        current_record = self.best_individual_scores[level_num]
        if current_record == None or time < current_record:
        
            utilities.log("***NEW LEVEL RECORD***\n" +
                    "Level " + str(level_num)+"'s record of " + 
                    str(utilities.format_time(current_record)) +
                    " broken with " + utilities.format_time(time) + "!")
                    
            self.best_individual_scores[level_num] = time
            if ghost_recorder != None:
                self.ghosts[level_num] = ghost_recorder.to_ghost()
            dirty = True
        else:
            utilities.log("Level " + str(level_num) + " completed! Time: "  + 
                    str(utilities.format_time(time)) + "\t Best: " + 
                    utilities.format_time(current_record))
            
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
                    utilities.log("***NEW FULL RUN RECORD***\n" + "Previous record " +
                            str(utilities.format_time(self.best_overall_run_total)) + 
                            " broken with " + str(utilities.format_time(final_time)))
                            
                    self.best_overall_run_total = final_time
                    self.best_overall_run_scores = [self.current_run_times[i] for i in range(0,self.get_num_levels())]
                    dirty = True
                else:
                    utilities.log("Game Completed! Final time: " + 
                            str(utilities.format_time(final_time)))
        
        if dirty:
            self.dump_highscores_to_file(0)
        
    def dump_highscores_to_file(self, suppress_printing=0):
        "0 = print nothing, 1 = print message, 2 = print entire file"
        if self.settings.edit_mode():
            utilities.log("Not saving high scores because we're in edit mode")
            return
        
        if suppress_printing > 0:
            utilities.log("Saving highscores to "+self.get_highscores_filename()+"...")
        highscores = LevelManager.generate_empty_highscores_dict(self.get_num_levels(), checksums=[])
        highscores["best_overall_run_total"] = utilities.format_time(self.best_overall_run_total)
        highscores["best_individual_scores"] = [utilities.format_time(self.best_individual_scores[i]) for i in range(0, self.get_num_levels())]
        highscores["best_overall_run_scores"] = [utilities.format_time(self.best_overall_run_scores[i]) for i in range(0, self.get_num_levels())]
        highscores["ghosts"] = [actors.Ghost.to_json(g) for g in self.ghosts]
        highscores["checksums"] = [self.get_checksum(i) for i in range(0, self.get_num_levels())]
        
        with open(self.get_highscores_filename(), 'w') as file:
            json_string = utilities.level_json_to_string(highscores)
            if suppress_printing > 1:
                utilities.log("writing text:\n" + json_string)
            file.write(json_string)
        
    def create_void_level(self):
        entity_list = [
                blocks.Block(0, 128, 128, 128),
                blocks.FinishBlock(56, -64, 16, 16)
        ]
        
        spawn_list = [actors.SpawnPoint(32, 96, "player")]
        theme_dict = BUILT_IN_THEMES
        filename = None
        
        return Level("The Void", entity_list, spawn_list, theme_dict, None)
        
    def read_filenames_from_header(self):
        res = []
        utilities.log("Reading " + self.file_dir + "/header.txt...")
        header = open(self.file_dir + "/header.txt")
        for line in header:
            if line[-1] == '\r':
                line = line[:len(line)-1]
            if line[-1] == '\n':
                line = line[:len(line)-1]
                
            res.append(line)
        
        to_log = "\tlevel filenames are:"
        for filename in res:
            to_log += "\n\t\t" + str(filename)
        utilities.log(to_log)
            
        return res
        
    def load_or_create_highscore_data(self):
        hs_dict = None
        if os.path.isfile("./"+self.get_highscores_filename()) and os.path.getsize("./"+self.get_highscores_filename()) > 0:
            utilities.log("Reading "+self.file_dir+"/highscores.json...")
            with open(self.file_dir+"/highscores.json") as data_file:
                hs_dict = json.load(data_file)
                hs_dict = self.repair_highscore_data_if_necessary(hs_dict)
        else:
            utilities.log("Creating " + self.file_dir+"/highscores.json...")
            num_levels = self.get_num_levels()
            hs_dict = LevelManager.generate_empty_highscores_dict(self.get_num_levels(), [])
            
            with open(self.file_dir+"/highscores.json", 'w') as file:
                json_str = json.dumps(hs_dict, indent=4, sort_keys=True)
                json_str = utilities.make_json_pretty(json_str)
                #json.dump(hs_dict, file, indent=4, sort_keys=True)
                file.write(json_str)
                
        return hs_dict
        
    @staticmethod
    def generate_empty_highscores_dict(num_levels, checksums):
        return {
                "best_overall_run_total":None,
                "best_overall_run_scores":[None for i in range(0,num_levels)],
                "best_individual_scores":[None for i in range(0,num_levels)],
                "checksums":checksums,
                "ghosts":[None for i in range(0, num_levels)]
            }
    
    def repair_highscore_data_if_necessary(self, highscore_data):
        num_levels = self.get_num_levels()
        actual_checksums = [self.get_checksum(i) for i in range(0, num_levels)]
        
        damaged = "checksums" not in highscore_data or len(highscore_data["checksums"]) != num_levels
        damaged |= "best_overall_run_scores" not in highscore_data or len(highscore_data["best_overall_run_scores"]) != num_levels
        damaged |= "best_individual_scores" not in highscore_data or len(highscore_data["best_individual_scores"]) != num_levels
        damaged |= "best_overall_run_total" not in highscore_data
        
        if damaged:
            utilities.log("highscores.json is invalid, wiping scores.")
            return LevelManager.generate_empty_highscores_dict(num_levels, actual_checksums)
        else:
            failed_checksums = []
            i = 0
            for (actual, given) in zip(actual_checksums, highscore_data["checksums"]):
                if actual != given:
                    failed_checksums.append(i)  
                i += 1
            
            if len(failed_checksums) > 0:
                utilities.log("checksums for levels didn't match: "+str(failed_checksums))
                utilities.log("wiping full run high score and individual records for affected levels.")
            
                highscore_data["best_overall_run_total"] = None
                highscore_data["best_overall_run_scores"] = [None]*num_levels
                for index in failed_checksums:
                    highscore_data["best_individual_scores"][index] = None
                    highscore_data["ghosts"][index] = None
                    highscore_data["checksums"][index] = actual_checksums[index]

        return highscore_data    
        
    def get_highscores_filename(self):
        return self.file_dir+"/highscores.json"
