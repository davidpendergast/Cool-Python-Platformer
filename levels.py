import sys
import json
from pprint import pprint

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
        self.level_highscore_data = []
        self.read_header()
        
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
        
        
        # self.level_num = num
        # self.actor = actor
        # self.level_name = "<Unnamed>"
            
        # file_name = self.file_dir + "/" + self.level_filenames[num]+".py"
        # print "exec-ing " + file_name
        # try:
            # execfile(file_name)
            # self.current_level = Level(group, self.level_name, self.level_num)
            # self.current_level.set_actor(self.actor)
        # except IOError:
            # print file_name+" could not be loaded. Please ensure that the file exists and is properly named."
            # self.load_void_level(actor, group)
        # except:
            # print file_name+" threw unexpected error while loading:", sys.exc_info()[0]
            # self.load_void_level(actor, group)
            
        
    def update_level_highscore(self, level_num, time):
        if len(self.level_highscore_data)-1 <= level_num:
            print "Error, could not update high score of level "+str(level_num)
        else:
            print "old time = "+str(self.level_highscore_data[level_num][0])+", new time = "+str(time)
            if self.level_highscore_data[level_num][0] > time:
                print "New High Score!"
                self.level_highscore_data[level_num] = (time, "DLP")
    
    def update_total_time_highscore(self, time):
        print "Total time = " + str(time)
        print str(self.level_highscore_data)
        if self.level_highscore_data[-1][0] > time:
            print "New High Score!"
            self.level_highscore_data[-1] = (time, "DLP");
                
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
            #e = sys.exc_info()[0]
            print "Error while loading "+filename+":"
            for err in sys.exc_info():
                print "\t"+str(err)
            
          
        return None
        
        
