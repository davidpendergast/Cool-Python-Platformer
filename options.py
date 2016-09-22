import json

class Settings:
    def __init__(self):
        with open("settings.json") as data_file:    
            data = json.load(data_file)
            self.__is_dev = data["dev_mode"]
            self.__level_path = data["level_path"] 
            
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
                 
class HardSettings:
    @staticmethod
    def standard_size():
        return (640, 480)
    @staticmethod
    def dev_size():
        return (840,680)
    @staticmethod
    def fps():
        return 60
        
        
        
        