import json
import os
from shutil import copyfile
import utilities
import random

## immutable settings

def standard_size():
    return (640, 480)
def dev_size():
    return (840,680)
def fps():
    return 60
    
edgy_titles = [
        "Xnoros", 
        "Fastbreak", 
        "Breakfast", 
        "Box Traversing Simulator 500", 
        "pygame platformer #214"
]
title_idx = random.randint(0, len(edgy_titles)-1)
    
def title():
    return edgy_titles[title_idx]
    

class Settings:
    default_settings_path = "configs/settings_default.json"
    local_settings_path = "configs/settings.json"
    
    def __init__(self):
        utilities.log("Reading " + Settings.default_settings_path + "...")
        with open(Settings.default_settings_path) as data_file:    
            data = json.load(data_file)
            self.__is_dev = data["dev_mode"]
            self.__level_path = data["level_path"] 
            self.__color = data["color"]
        
        self.create_local_settings_if_needed()
        utilities.log("Reading " + Settings.local_settings_path + "...")
        with open(Settings.local_settings_path) as data_file:
            data = json.load(data_file)
            if "dev_mode" in data: self.__is_dev = data["dev_mode"]
            if "level_path" in data: self.__level_path = data["level_path"]
            if "color" in data: self.__color = data["color"]
            
        self.__show_grid = False
        self.__invincible_mode = False
        self.__frozen_mode = False  
    def dev_mode(self):
        return self.__is_dev
    def level_path(self):
        return self.__level_path
    def show_grid(self):
        return self.__show_grid
    def set_show_grid(self, val):
        self.__show_grid = val
    def invincible_mode(self):
        self.__invincible_mode
    def set_invincible_mode(self, val):
        if self.dev_mode():
            self.__invincible_mode = val
    def frozen_mode(self):
        return self.__frozen_mode
    def set_frozen_mode(self, val):
        if self.dev_mode():
            self.__frozen_mode = val   
    def get_color(self):
        return self.__color
    def create_local_settings_if_needed(self):
        if os.path.isfile(Settings.local_settings_path):
            return
        else:
            utilities.log("Creating " + Settings.local_settings_path + "...")
            copyfile(Settings.default_settings_path, Settings.local_settings_path)
                 
