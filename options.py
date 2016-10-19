import json
import os
from shutil import copyfile
import utilities
import random
import keybindings

## immutable settings

def standard_size():
    return (640, 480)
def dev_size():
    return (840,680)
def fps():
    return 60
    
_edgy_titles = [
        "Block Traversing Simulator 500",
        "Between a Block and a Hard Place",
        "Block Paper Scissors"
]
title_idx = random.randint(0, len(_edgy_titles)-1)
    
def title():
    return _edgy_titles[title_idx]
    

class Settings:
    default_settings_path = "configs/settings_default.json"
    local_settings_path = "configs/settings.json"
    
    def __init__(self):
        utilities.log("Reading " + Settings.default_settings_path + "...")
        with open(Settings.default_settings_path) as data_file:    
            self.default_settings = json.load(data_file)
        
        self.create_local_settings_if_needed()
        utilities.log("Reading " + Settings.local_settings_path + "...")
        with open(Settings.local_settings_path) as data_file:
            self.local_settings = json.load(data_file)
            
        ## temporary settings
        self._show_grid = False
        self._invincible_mode = False
        self._frozen_mode = False  
        self._show_spawns = self.dev_mode()
        self._show_paths = self.dev_mode()
        self._draw_3d = self._get_attribute("add_whole_new_dimension_of_gameplay")
        
        self.bindings = keybindings.KeyBindings(self)
        
    def _get_attribute(self, outer_key, inner_key=None):
        if inner_key != None:
            if outer_key in self.local_settings and inner_key in self.local_settings[outer_key]:
                return self.local_settings[outer_key][inner_key]
            elif outer_key in self.default_settings and inner_key in self.default_settings[outer_key]:
                return self.default_settings[outer_key][inner_key]
        else:
            if outer_key in self.local_settings:
                return self.local_settings[outer_key]
            elif outer_key in self.default_settings:
                return self.default_settings[outer_key]
    def _set_attribute(self, value, outer_key, inner_key=None):
        if inner_key != None:
            self.local_settings[outer_key][inner_key] = value
        else:
            self.local_settings[outer_key] = value
    def dev_mode(self):
        return self._get_attribute("dev_mode")
    def level_path(self):
        return self._get_attribute("level_path")
    def show_grid(self):
        return self._show_grid
    def draw_3d(self):
        return self._draw_3d
    def set_draw_3d(self, val):
        self._draw_3d = val
    def show_spawns(self):
        return self._show_spawns
    def show_paths(self):
        return self._show_paths
    def set_show_grid(self, val):
        self._show_grid = val
    def invincible_mode(self):
        self._invincible_mode
    def set_invincible_mode(self, val):
        if self.dev_mode():
            self._invincible_mode = val
    def frozen_mode(self):
        return self._frozen_mode
    def set_frozen_mode(self, val):
        if self.dev_mode():
            self._frozen_mode = val   
    def get_color(self):
        return self._get_attribute("color")
    def get_keybinding(self, action):
        "returns the list of keys bound to an action"
        binding = self._get_attribute("keybindings", action)
        
        if not isinstance(binding, list):
            return [binding]
        else:
            return binding
            
    def set_keybinding(self, action, value):
        self._set_attribute(value, "keybindings", action)
    
    def get_actions_for_key(self, key):
        return self.bindings.get_actions_for_key(key)
        
    def create_local_settings_if_needed(self):
        if os.path.isfile(Settings.local_settings_path):
            return
        else:
            utilities.log("Creating " + Settings.local_settings_path + "...")
            copyfile(Settings.default_settings_path, Settings.local_settings_path)
                 
