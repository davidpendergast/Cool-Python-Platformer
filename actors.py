import pygame 
import sets 
import math

import paths
import utilities
import blocks

class Actor(blocks.Box):
    STANDARD_SIZE = (24, 32)
    
    def __init__(self, width=24, height=32, color=(255, 128, 128)):
        blocks.Box.__init__(self, width, height, color)
        # Actor collision state variables.
        # Note: these are reset to false on each actor update, and reapplied by the collision fixer.
        self.is_grounded = False        # is touching a solid box that's below
        self.is_left_walled = False     # is touching a solid box on the left
        self.is_right_walled = False    # is touching a solid box on the right
        self.is_left_toe_grounded = False
        self.is_right_toe_grounded = False
        
        self.wall_stick_time = 0
        self.jumps = 0
        
        self.wall_release_time = 5      # actor will stick to wall for X frames before letting go.
        self.wall_hang_friction = 0.1   # vertical friction actor applies when hanging on a wall.
        self.is_alive = True
        self.is_crushed = False
        self.is_player = False
        self.finished_level = False
        
        self.jump_speed = -7
        self.max_vx = 4             # 'run' speed
        self.move_speed = 2         # 'dash' speed
        self.air_move_speed = 0.5   # degree of aerial control the player has over the character

    def reset(self):
        self.jumps = 0
        self.wall_stick_time = 0
        self.is_alive = True
        self.is_grounded = False
        self.is_left_walled = False
        self.is_right_walled = False
        self.is_left_toe_grounded = False
        self.is_right_toe_grounded = False
        self.is_crushed = False
        self.finished_level = False
        self.v = (0, 0)
        self.a = (0, 0.3)
        
    def kill(self, message="unknown causes."):
        self.is_alive = False
        utilities.log(str(self)+" was killed by "+message)
        
    def jump_action(self):
        if self.is_grounded == False:   # if not grounded, check for walljumps
            if self.is_left_walled:
                self.set_vy(self.jump_speed)
                self.set_vx(-10*self.jump_speed)
                return 
            elif self.is_right_walled:
                self.set_vy(self.jump_speed)
                self.set_vx(10*self.jump_speed)
                return
        
        if self.jumps > 0:  # otherwise use a normal jump (even if not grounded.)
            self.set_vy(self.jump_speed)
            self.jumps = self.jumps - 1
        
    def move_action(self, dir):
        "if dir > 0, moves actor right. If dir < 0 moves left. Otherwise actor will not move."
        
        if self.is_grounded:
            if self.v[0] < self.move_speed and self.v[0] > -self.move_speed: 
                # making a grounded actor immediately dash
                self.v = (self.move_speed*dir, self.v[1])
            self.a = (0.4*dir, self.a[1])
        else:
            if (self.is_left_walled and dir > 0) or (self.is_right_walled and dir < 0):
                if self.wall_stick_time >= self.wall_release_time:
                    self.wall_stick_time = 0
                    self.set_vx(self.vx() + dir*self.air_move_speed)
                else:
                    self.wall_stick_time += 1
            else:
                self.set_vx(self.vx() + dir*self.air_move_speed)
        
    def update(self, dt):
        if not self.is_right_walled and not self.is_left_walled:
            self.wall_stick_time = 0
        if not self.is_grounded:    # if player has left ground, there shouldn't be any horizontal acceleration
            self.set_ax(0)
        
        self.is_grounded = False
        self.is_left_walled = False
        self.is_right_walled = False
        self.is_left_toe_grounded = False
        self.is_right_toe_grounded = False
        
        blocks.Box.update(self, dt)
        
        #fall detection
        if self.y() >= 2048:
            self.kill("falling too far.")

    def collided_with(self, obj, dir="NONE"):
        if obj.is_solid:
            if dir == "BOTTOM":
                self.jumps = 1
    
    def apply_friction(self, dt):
        fric = 0.1
        if self.is_grounded:
            fric = 1
        vx = self.vx()
        if vx < fric and vx > -fric:
            vx = 0
        else:
            if vx < 0:
                vx = vx + fric
            else:
                vx = vx - fric
        self.set_vx(vx)
            
    def get_update_priority(self):
        return 1
        
    def is_actor(self): return True
        
    def __repr__(self):
        if self.is_player:
            return "Player"+self.rect_str()
        else:
            return "Actor"+self.rect_str()
        
        
class Enemy(Actor):
    NORMAL_COLOR = (255, 0, 255)
    SMART_COLOR = (0, 125, 125)
    BAD_COLOR = (255, 0, 0)
    
    def __init__(self, width, height, color=(255, 0, 255)):
        Actor.__init__(self, width, height, color)
        self.max_vx = 1
        self.move_speed = 0.5
        self.direction = -1
        
        self.walks_off_platforms = True
        self.is_stompable = True
        
    def update(self, dt):
        if not self.is_alive:
            return;
        if not self.walks_off_platforms and self.is_grounded:
            if (self.direction == -1 and not self.is_left_toe_grounded) or (self.direction == 1 and not self.is_right_toe_grounded):
                self.direction = -1*self.direction
        Actor.update(self, dt)
        
        self.move_action(self.direction)
        
    def get_update_priority(self):
        return 2
        
    def collided_with(self, obj, dir="NONE"):
        if not self.is_alive:
            return
        Actor.collided_with(self, obj, dir)
        if obj.is_actor():
            if obj.is_player:
                if self.is_stompable and dir == "TOP":
                    self.kill(" smushing.")
                    obj.set_vy(obj.jump_speed / 2)
                    if obj.jumps == 0:
                        obj.jumps = 1
                else:
                    # kill the player
                    obj.kill(" an enemy.")
        elif obj.is_solid and (dir == "RIGHT" or dir == "LEFT"):
            self.direction = -self.direction
            
    def is_enemy(self): return True    
         
    def to_json(self):
        my_type = "dumb"
        if not self.is_stompable:
            my_type = "bad"
        elif not self.walks_off_platforms:
            my_type = "smart"
        
        return {
            "type":my_type,
            "width":self.width(),
            "height":self.rect.height,
            "theme":self.get_theme_id()
        }
        
    @staticmethod    
    def from_json(json_data):
        result = Enemy(json_data["width"], json_data["height"])
        result.is_stompable = (json_data["type"] in ("smart", "dumb"))
        result.walks_off_platforms = json_data["type"] == "dumb"
        result.set_theme_id(json_data["theme"] if "theme" in json_data else "default")
        return result
        
    def __repr__(self):
        return "Enemy"+self.rect_str()
            
    @staticmethod
    def get_stupid_walker_enemy(x, y, direction = -1):
        res = Enemy(Actor.STANDARD_SIZE[0], Actor.STANDARD_SIZE[1])
        res.set_xy(x, y)
        res.direction = direction
        res.walks_off_platforms = True
        return res
        
    @staticmethod
    def get_smart_walker_enemy(x, y, direction=-1):
        res = Enemy.get_stupid_walker_enemy(x, y, direction)
        res.walks_off_platforms = False
        res.color = Enemy.SMART_COLOR
        return res
        
    @staticmethod
    def get_bad_enemy(x, y, smart=True, direction=-1):
        if smart:
            res = Enemy.get_smart_walker_enemy(x, y, direction)
        else:
            res = Enemy.get_stupid_walker_enemy(x, y, direction)
        res.color = Enemy.BAD_COLOR
        res.is_stompable = False
        return res
            
            
class GhostRecorder:
    def __init__(self, actor_to_track):
       self.actor_to_track = actor_to_track
       self.x_points = []
       self.y_points = []
    
    def update(self, dt):
        if self.actor_to_track.is_alive:
            self.x_points.append(self.actor_to_track.x())
            self.y_points.append(self.actor_to_track.y())
            
    def to_ghost(self):
        return Ghost(self.x_points, self.y_points, self.actor_to_track.get_color())
    
    def clear(self):
        self.x_points = []
        self.y_points = []

class Ghost(Actor):
    def __init__(self, x_points, y_points, color):
        Actor.__init__(self)
        self.is_solid = False
        self.set_color(color)
        self.x_points = x_points
        self.y_points = y_points
        self.index = 0

    def update(self, dt):
        self.index += 1
        if self.index >= len(self.x_points):
            self.is_alive = False
        else:
            self.set_x(self.x_points[self.index])
            self.set_y(self.y_points[self.index])
    
    def reset(self):
        self.is_alive = True
        self.index = 0
        
    def is_ghost(self):
        return True
    
    @staticmethod
    def from_json(json_data):
        if json_data == None:
            return None
        x_points = json_data["x_points"]
        y_points = json_data["y_points"]
        color = json_data["color"]
        
        return Ghost(x_points, y_points, color)
    
    
    @staticmethod
    def to_json(ghost):
        if ghost == None:
            return None
        else:
            c = ghost.get_color()
            return {
                "x_points":ghost.x_points,
                "y_points":ghost.y_points,
                "color":[c[0], c[1], c[2]]
            }

class SpawnPoint(blocks.Box):
    def __init__(self, x, y, actor):
        blocks.Box.__init__(self, 10, 10)
        self.set_xy(x,y)
        self.actor = actor
        self.is_solid = False
        self.is_pushable = False
        self.is_visible = False
        self.has_physics = False
        
    def do_spawn(self):
        actor = self.get_actor()
        actor.reset()
        actor.set_xy(self.x(), self.y()) 
        
    def get_actor(self):
        if self.actor == "player":
            self.actor = Actor()
            self.actor.is_player = True
            self.actor.set_theme_id("default")
        return self.actor
        
    def is_spawn_point(self): return True
    
    def __repr__(self):
        return "Spawn"+self.rect_str()
        
    def to_json(self):
        if isinstance(self.actor, basestring):
            actor_json = self.actor
        elif self.actor.is_player:
            actor_json = "player"
        else:
            actor_json = self.actor.to_json()
        return {
            "type":"spawn",
            "x":self.x(),
            "y":self.y(),
            "actor":actor_json
        }
    
    @staticmethod
    def from_json(json_data):
        x = json_data["x"]
        y = json_data["y"]
        if json_data["actor"] == "player":
            actor = "player"
        else: 
            actor = Enemy.from_json(json_data["actor"])
        return SpawnPoint(x, y, actor)
        
