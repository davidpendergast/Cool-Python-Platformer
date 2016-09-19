import sys
import json
import os
from pprint import pprint
from StringIO import StringIO

import pygame

import phys_objects
import equations


# Level class is essentially just a list of the entities in a level, as well as information 
# about the level including its name and number.
class Level:
        def __init__(self, list, name):
            self.name = name
            self.num = -1
            
            self.entity_list = list[:]
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
          

class LevelManager:
    def __init__(self, file_dir):
        self.level_num = 0
        self.current_level = None
        
        self.file_dir = file_dir    # "levels/something", most likely
        self.level_filenames =[]
        self.read_header()
        self.highscores = self.load_or_create_highscore_data()  
        
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
        pass
    
    def update_total_time_highscore(self, time):
        pass
                
    def create_void_level(self):
        list = []
       
        list.append(phys_objects.Block(128, 128).set_xy(0, 128))
        list.append(phys_objects.FinishBlock(16, 16).set_xy(56, -64))
        
        actor = phys_objects.Actor().set_xy(32, 96)
        actor.is_player = True
        list.append(actor)
        
        return Level(list, "The Void")
        
    def read_header(self):
        header = open(self.file_dir + "/header.txt")
        for line in header:
            if line[-1] == '\r':
                line = line[:len(line)-1]
            if line[-1] == '\n':
                line = line[:len(line)-1]
                
            self.level_filenames.append(line)
        
        print "Level filenames are "+str(self.level_filenames)
        
    def load_or_create_highscore_data(self):
        if os.path.isfile("./"+self.file_dir+"/highscores.json"):
            pass
        else:
            print "No highscores.json file found, creating new one..."
            num_levels = len(self.level_filenames)
            dict = {
                "best_overall_run_total":None,
                "best_overall_run_scores":[None for i in range(0,num_levels)],
                "best_individual_scores":[None for i in range(0,num_levels)]
            }
            
            file = open(self.file_dir+"/highscores.json", 'w')
            
            io = StringIO()
            print "dumping: "
            print json.dumps(dict, indent=4, sort_keys=True)
            
            json.dump(dict, file, indent=4, sort_keys=True)
            
            file.close()
            

class LevelReader:
    @staticmethod
    def load(filename):
        list = []
        
        try:
            with open(filename) as json_file:
                print str(json_file)
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
                            x_path = equations.Expression.get_expression(str(elem["x_path"]))
                            y_path = equations.Expression.get_expression(str(elem["y_path"]))
                            path = phys_objects.Path(x_path, y_path)
                        elif "x_points" in elem and "y_points" in elem and "speed" in elem:
                            x_points = elem["x_points"]
                            y_points = elem["y_points"]
                            speed = elem["speed"]
                            print str(x_points) + ", " + str(y_points) +", " + str(speed)
                            path = phys_objects.PointPath(x_points, y_points, speed)
                        
                        block = phys_objects.MovingBlock(int(elem["width"]), int(elem["height"]), path)
                    else:
                        continue
                    list.append(block)
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
                    list.append(enemy)
            else:
                print "no enemies in "+filename+"?"
            
            actor = phys_objects.Actor().set_xy(int(data["actor"]["x"]), int(data["actor"]["y"]))
            actor.is_player = True
            
            list.append(actor)
            
            return Level(list, name)
        except:
            print "Error while loading "+filename+":"
            for err in sys.exc_info():
                print "\t"+str(err)
            
          
        return None
        
        
