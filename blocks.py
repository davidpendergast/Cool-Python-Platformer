import pygame 
import sets 
import math

import equations
import paths
import utilities

class Box(pygame.sprite.Sprite):
    def __init__(self, width, height, color=(128, 128, 128)):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((width, height))
        self.color = color
        self.repaint()
        
        self.is_solid = True        # Whether this box prevents movement of other solid boxes
        self.is_pushable = True     # Whether the collision fixer can move this object
        self.is_visible = True      # Whether this box renders.
        self.has_physics = True
        
        self.rect = pygame.Rect(0, 0, width, height)
        self.v = (0, 0)
        self.a = (0, 0.3)
        
        self.max_vy = 10
        self.max_vx = 5
        
        self.rf_parent = None           # physics reference frame information. For example, when an actor stands on a moving platform
        self.rf_children = sets.Set()   # or is stuck to another object, it will enter that object's reference frame.
        self.theme_id = None
        
    def update(self, dt):
        if self.has_physics:
            self.apply_physics(dt)
        
    def apply_physics(self, dt):
        vx = self.v[0] + self.a[0]*dt
        if vx > self.max_vx:
            vx = self.max_vx
        elif vx < -self.max_vx:
            vx = -self.max_vx
        self.v = (vx, self.v[1] + self.a[1]*dt) 
        if abs(vx) < 1:
            vx = 0
        self.move(vx*dt, self.v[1]*dt, True)
        
    def move(self, dx, dy, move_at_least_1=False):
        "Moves this object and all children in reference frame"
        if move_at_least_1 and dx != 0 and abs(dx) < 1:
            dx = math.copysign(1, dx)
        if move_at_least_1 and dy != 0 and abs(dy) < 1:
            dy = math.copysign(1, dy) 
        self.rect.move_ip(dx, dy)
        for kid in self.rf_children:
            kid.rect.move_ip(dx, dy)
            
    def set_x(self, x):
        dx = x - self.x()
        self.move(dx, 0)
        return self
        
    def set_y(self, y):
        dy = y - self.y()
        self.move(0, dy)
        return self
        
    def set_xy(self, x, y):
        self.set_x(x)
        self.set_y(y)
        return self
        
    def x(self):
        return self.rect.x
        
    def y(self):
        return self.rect.y
        
    def width(self):
        return self.rect.width
    
    def height(self):
        return self.rect.height
        
    def get_xy(self):
        return (self.x(), self.y())
        
    def set_vx(self, vx):
        if vx > self.max_vx:
            vx = self.max_vx
        elif vx < -self.max_vx:
            vx = -self.max_vx
        self.v = (vx, self.v[1])
        
    def set_vy(self, vy):
        if vy > self.max_vy:
            vy = self.max_vy
        elif vy < -self.max_vy:
            vy = -self.max_vy
        self.v = (self.v[0], vy)
        
    def vx(self):
        return self.v[0]
        
    def vy(self):
        return self.v[1]
        
    def set_ax(self, ax):
        self.a = (ax, self.a[1])
        
    def add_to_rf(self, other):
        other.rf_parent = self
        self.rf_children.add(other)
        
    def remove_from_rf(self, other):
        assert other.rf_parent == self and other in self.rf_children, "Error: Attempting disjointed rf removal"
        other.rf_parent = None
        self.rf_children.remove(other)
        
    def is_still_rf_child_of(self, parent):
        assert self.rf_parent == parent, "Error: Disjointed rf parent-child check"
        bool = self.rect.left < parent.rect.right and self.rect.right > parent.rect.left    #horizontally aligned
        bool = bool and abs(self.rect.bottom - parent.rect.top) < 0.5                       #directly on top of parent
        return bool
        
    def collided_with(self, obj, direction="NONE"):
        "direction = side of self that touched obj. Valid inputs are TOP, BOTTOM, LEFT, RIGHT, NONE"
        pass
    
    def get_color(self):
        return self.color
    
    def set_color(self, color, perturb_color=0, only_greyscale=True):
        self.color = utilities.perturb_color(color, perturb_color, only_greyscale)
        self.repaint()
    
    def set_theme_id(self, id):
        self.theme_id = id
        
    def get_theme_id(self):
        return self.theme_id
    
    def repaint(self):
        self.image.fill(self.color, (0, 0, self.image.get_width(), self.image.get_height()))
        
    def __cmp__(self, other):
        if isinstance(other, Box):
            return self.get_update_priority() - other.get_update_priority() 
        else:
            return 1
    
    def get_update_priority(self):
        return -1
    
    def __str__(self):
        return "Box"+self.rect_str()
        
    def rect_str(self):
        return "[" +str(self.x()) +", "+str(self.y())+", "+str(self.width())+", "+str(self.height())+"]"
        
    def to_json(self):
        raise NotImplementedError("Cannot convert "+str(self)+" to json because to_json isn't implemented.")
        
    def is_block(self): return False
    def is_actor(self): return False
    def is_moving_block(self): return False
    def is_bad_block(self): return False
    def is_finish_block(self): return False
    def is_enemy(self): return False
    def is_ghost(self): return False
    def is_spawn_point(self): return False
    
    
class Block(Box):
    BAD_COLOR = (255, 0, 0)
    NORMAL_COLOR = (128, 128, 128)
    
    def __init__(self, width, height, color=None): 
        color = Block.NORMAL_COLOR if color == None else color
        Box.__init__(self, width, height, color)
        self.is_solid = True
        self.is_pushable = False
        self.is_visible = True
        self.has_physics = False
        self.a = (0, 0)
    
    def update(self, dt):
        pass
        
    def get_update_priority(self):
        return 5
        
    def is_block(self): return True
    
    def to_json(self):
        result = {
            "type":"normal",
            "width":self.width(),
            "height":self.height(),
            "x":self.x(),
            "y":self.y()
        }
        
        if self.get_theme_id() != "default":
            result["theme"] = self.get_theme_id()
            
        return result
    
    @staticmethod
    def from_json(json_data):
        result = Block(json_data["width"], json_data["height"])
        result.set_xy(json_data["x"], json_data["y"])
        result.set_theme_id(json_data["theme"] if "theme" in json_data else "default")
        return result
        
    def __str__(self):
        return "Block"+self.rect_str()
        
class MovingBlock(Block):
    def __init__(self, width, height, path, color=None):
        Block.__init__(self, width, height, color)
        self.path = path
    
    def update(self, dt):
        self.v = (0,0)
        if self.path != None:
            old_x = self.x()
            old_y = self.y()
           
            self.path.step(dt)
            xy = self.path.get_xy()
            self.set_x(xy[0])
            self.set_y(xy[1])
            
            self.v = (self.x() - old_x, self.y() - old_y) # used for crushing 
    
    def get_update_priority(self):
        return 4
        
    def is_moving_block(self): return True
    
    def to_json(self):
        my_json = {
            "type":"moving",
            "width":self.width(),
            "height":self.height(),
            "path":self.path.to_json()
        }
        if self.get_theme_id() != "default":
            my_json["theme"] = self.get_theme_id()
            
        return my_json
        
    @staticmethod
    def from_json(json_data):
        path = paths.from_json(json_data["path"])
        result = MovingBlock(int(json_data["width"]), int(json_data["height"]), path)
        result.set_theme_id(json_data["theme"] if "theme" in json_data else "default")
        return result
        
    def __str__(self):
        return "Moving_Block"+self.rect_str()
        

class BadBlock(Block):
    def __init__(self, width, height, color=None):
        color = Block.BAD_COLOR if color == None else color
        Block.__init__(self, width, height, color)
    
    def collided_with(self, obj, dir="NONE"):
        if obj.is_actor():
            obj.kill("touching a bad block.")
            
    def get_update_priority(self):
        return 3
        
    def is_bad_block(self): return True
    
    def to_json(self):
        my_json = Block.to_json(self)
        my_json['type'] = "bad"
        
        if self.get_theme_id() != "default":
            my_json["theme"] = self.get_theme_id()
            
        return my_json
    
    @staticmethod
    def from_json(json_data):
        result = BadBlock(json_data["width"], json_data["height"])
        result.set_xy(json_data["x"], json_data["y"])
        result.set_theme_id(json_data["theme"] if "theme" in json_data else "default")
        return result
        
    def __str__(self):
        return "Bad_Block"+self.rect_str()
        
        
class FinishBlock(Block):
    def __init__(self, width=16, height=16, color=(0, 255, 0)):
        Block.__init__(self, width, height, color)
        
    def collided_with(self, obj, dir="NONE"):
        if obj.is_actor():
            obj.finished_level = True
    
    @staticmethod
    def from_json(json_data):
        result = FinishBlock(json_data["width"], json_data["height"])
        result.set_theme_id(json_data["theme"] if "theme" in json_data else "default")
        result.set_xy(json_data["x"], json_data["y"])
        return result
        
    def to_json(self):
        result = {
            "type":"finish",
            "x":self.x(),
            "y":self.y(),
            "width":self.width(),
            "height":self.height()
        }
        
        if self.get_theme_id() != "default":
            result["theme"] = self.get_theme_id()
            
        return result
            
    def is_finish_block(self): return True
    
    def __str__(self):
        return "Finish_Block"+self.rect_str()   

        
class BlockFactory:
    CONSTRUCTORS = {
        "normal":Block.from_json,
        "finish":FinishBlock.from_json,
        "bad":BadBlock.from_json,
        "moving":MovingBlock.from_json
    }
    @staticmethod
    def from_json(json_data):
        block_type = json_data["type"]
        if block_type in BlockFactory.CONSTRUCTORS:
            return BlockFactory.CONSTRUCTORS[block_type](json_data)
        else:
            raise ValueError("Unrecognized block type: "+str(block_type))