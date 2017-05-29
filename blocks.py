import pygame 
import sets 
import math

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
        self.theme_id = "default"
        
    def update(self, dt):
        if self.has_physics:
            self.apply_physics(dt)
    
    def alive(self):
        return not hasattr(self, "is_alive") or self.is_alive
        
    def apply_physics(self, dt):
        vx = self.vx() + self.a[0]*dt
        vy = self.vy() + self.a[1]*dt
        self.set_vx(vx)
        self.set_vy(vy)
        if abs(vx) < 1:
            vx = 0
        self.move(vx*dt, self.vy()*dt, True)
        
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
    
    def set_size(self, width, height):
        "-1 = no change"
        if width != -1:
            self.rect.width = width
        if height != -1:
            self.rect.height = height
        self.image = pygame.Surface((self.width(), self.height()))
        self.repaint()
        
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
    
    def __eq__(self, other):
        return self is other
    
    def __repr__(self):
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
    def is_particle(self): return False
    
    def get_update_priority(self):
        if self.is_actor():
            return 1
        elif self.is_bad_block():
            return 3
        elif self.is_moving_block():
            return 4
        else:
            return 5
    
    
class Block(Box):
    BAD_COLOR = (255, 0, 0)
    NORMAL_COLOR = (128, 128, 128)
    
    def __init__(self, x, y, width, height, color=None): 
        color = Block.NORMAL_COLOR if color == None else color
        Box.__init__(self, width, height, color)
        self.is_solid = True
        self.is_pushable = False
        self.is_visible = True
        self.has_physics = False
        self.a = (0, 0)
        
        self._path = None
        self._initial_xy = (x, y)
        self.set_xy(x, y)
    
    def set_path(self, path):
        self._path = path
        
    def get_path(self):
        return self._path
        
    def set_x_initial(self, x):
        self._initial_xy = (x, self._initial_xy[1])
        
    def set_y_initial(self, y):
        self._initial_xy = (self._initial_xy[0], y)
    
    def x_initial(self):
        return self._initial_xy[0]
        
    def y_initial(self):
        return self._initial_xy[1]
        
    def xy_initial(self):
        return self._initial_xy
    
    def update(self, dt):
        if self._path != None:
            self.v = (0,0)
            old_x = self.x()
            old_y = self.y()
           
            self._path.step(dt)
            xy = self._path.get_xy()
            self.set_x(self.x_initial() + xy[0])
            self.set_y(self.y_initial() + xy[1])
            
            self.v = (self.x() - old_x, self.y() - old_y) # used for crushing 
        
    def is_block(self): return True
    def is_moving_block(self): return self._path != None
    
    def to_json(self):
        result = {
            "type":"normal",
            "width":self.width(),
            "height":self.height(),
            "x":self.x_initial(),
            "y":self.y_initial()
        }
        
        if self.get_theme_id() != "default":
            result["theme"] = self.get_theme_id()
        if self._path != None:
            result["path"] = self._path.to_json()
            
        return result
    
    @staticmethod
    def from_json(json_data):
        return Block(json_data["x"], json_data["y"], json_data["width"], json_data["height"])
        
    def __repr__(self):
        return "Block"+self.rect_str()
        

class BadBlock(Block):
    def __init__(self, x, y, width, height, color=None):
        color = Block.BAD_COLOR if color == None else color
        Block.__init__(self, x, y, width, height, color)
    
    def collided_with(self, obj, dir="NONE"):
        if obj.is_actor():
            obj.kill("touching a bad block.")
            
    def is_bad_block(self): return True
    
    def to_json(self):
        my_json = Block.to_json(self)
        my_json['type'] = "bad"
            
        return my_json
    
    @staticmethod
    def from_json(json_data):
        return BadBlock(json_data["x"], json_data["y"], json_data["width"], json_data["height"])
        
    def __repr__(self):
        return "Bad_Block"+self.rect_str()
        
        
class FinishBlock(Block):
    def __init__(self, x, y, width=16, height=16, color=(0, 255, 0)):
        Block.__init__(self, x, y, width, height, color)
        
    def collided_with(self, obj, dir="NONE"):
        if obj.is_actor():
            obj.finished_level = True
    
    @staticmethod
    def from_json(json_data):
        return FinishBlock(json_data["x"], json_data["y"], json_data["width"], json_data["height"])
        
    def to_json(self):
        my_json = Block.to_json(self)
        my_json['type'] = "finish"
            
        return my_json
            
    def is_finish_block(self): return True
    
    def __repr__(self):
        return "Finish_Block"+self.rect_str()   

        
class BlockFactory:
    CONSTRUCTORS = {
        "normal":Block.from_json,
        "finish":FinishBlock.from_json,
        "bad":BadBlock.from_json
    }
    @staticmethod
    def from_json(json_data):
        block_type = json_data["type"]
        
        if block_type in BlockFactory.CONSTRUCTORS:
            block = BlockFactory.CONSTRUCTORS[block_type](json_data)
            if "theme" in json_data:
                block.set_theme_id(json_data["theme"])
            if "path" in json_data:
                block.set_path(paths.from_json(json_data["path"]))
            return block
        else:
            raise ValueError("Unrecognized block type: "+str(block_type))
