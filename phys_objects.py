import pygame 
import sets 
import math

import equations
import paths
from utilities import Utils

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
        self.color = Utils.perturb_color(color, perturb_color, only_greyscale)
        self.repaint()
        
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
        return "Box"
        
    def is_block(self): return False
    def is_actor(self): return False
    def is_moving_block(self): return False
    def is_bad_block(self): return False
    def is_finish_block(self): return False
    def is_enemy(self): return False
    def is_ghost(self): return False
    
    
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
        
    def __str__(self):
        return "Block"
        
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
        
    def __str__(self):
        return "Moving_Block"
    
    
class Actor(Box):
    STANDARD_SIZE = (24, 32)
    
    def __init__(self, width=24, height=32, color=(255, 128, 128)):
        Box.__init__(self, width, height, color)
        
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
        print str(self)+" was killed by "+message
        
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
        
        Box.update(self, dt)
        
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
        
    def __str__(self):
        if self.is_player:
            return "Player"
        else:
            return "Actor"
        
        
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
        
    def __str__(self):
        return "Bad_Block"
        
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
            print "I'm dead! no colliding for me today!"
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
         
    def __str__(self):
        return "Enemy"
            
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

        
class FinishBlock(Block):
    def __init__(self, width=16, height=16, color=(0, 255, 0)):
        Block.__init__(self, width, height, color)
        
    def collided_with(self, obj, dir="NONE"):
        if obj.is_actor():
            obj.finished_level = True
            
    def is_finish_block(self): return True
    
    def __str__(self):
        return "Finish_Block"    
            
            
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
        
        # if len(x_points) != len(y_points):
            # raise ValueError("Unequal array sizes for Ghost: "+str(len(x_points)+" != "+str(len(y_points))

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
        
