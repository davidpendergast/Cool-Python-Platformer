import pygame 
import sets 
import math

import equations
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
        return "Box"+str(self.get_xy())
        
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
        return "Block"+str(self.get_xy())
        
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
        return "Moving_Block"+str(self.get_xy())
    
    
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
            return "Player"+str(self.get_xy())
        else:
            return "Actor"+str(self.get_xy())
        
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
        return "Bad_Block"+str(self.get_xy()) 
        
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
                    print "dir="+dir
                    obj.kill(" an enemy.")
        elif obj.is_solid and (dir == "RIGHT" or dir == "LEFT"):
            self.direction = -self.direction
            
    def is_enemy(self): return True    
         
    def __str__(self):
        return "Enemy"+str(self.get_xy()) 
            
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
        return "Finish_Block"+str(self.get_xy())        
            
class CollisionFixer:
    def __init__(self):
        self.thresh = 0.4
        
    def solve_collisions(self, group):
        unmovables = []
        movables = []
        actors = []
        
        for sprite in group:
            if sprite.is_solid == False:
                continue
            elif sprite.is_pushable:
                movables.append(sprite)
                if sprite.is_actor():
                    actors.append(sprite)
            else:
                unmovables.append(sprite)
        
        for sprite in movables: # solving movable-unmovable coliisions
            colliding_with = [x for x in unmovables if self.really_intersects(sprite.rect, x.rect, self.thresh)]
            for other in colliding_with:
                self.solve_pushout_collision(other, sprite)
        
        for sprite in actors:   # Checking for crushed actors
            colliding_with = [x for x in unmovables if self.really_intersects(sprite.rect, x.rect, self.thresh)]
            for obj in colliding_with:
                direction = self.intersect_dir(obj.rect, sprite.rect, self.thresh)
                if direction != None and direction != "NONE":
                    crushed = (direction == "TOP" and obj.vy() > 0) or \
                        (direction == "BOTTOM" and obj.vy() < 0) or \
                        (direction == "LEFT" and obj.vx() > 0) or \
                        (direction == "RIGHT" and obj.vx() < 0)
                    if crushed:
                        sprite.is_crushed = True
                        break
                    
        for sprite in actors: # Setting is_grounded, is_left_walled, is_right_walled for each actor
            full_rect = sprite.rect
            bot_rect  = pygame.Rect(full_rect.x, full_rect.bottom, full_rect.width, 1).inflate(-full_rect.width*self.thresh, 0) # creating a skinny rect that lies directly underneath the sprite.
            left_rect = pygame.Rect(full_rect.x-1, full_rect.y, 1, full_rect.height).inflate(0, -full_rect.height*self.thresh)
            right_rect= pygame.Rect(full_rect.right, full_rect.y, 1, full_rect.height).inflate(0, -full_rect.height*self.thresh)
            
            candidates = self.rect_collide(full_rect.inflate(2, 2), unmovables)
            
            bot_collisions = self.rect_collide(bot_rect, candidates)
            if len(bot_collisions) > 0:
                sprite.is_grounded = True
                for othersprite in bot_collisions:  # setting toe collision states
                    coll = self.rect_intersect(othersprite.rect, bot_rect)
                    
                    if coll.left == bot_rect.left:
                        sprite.is_left_toe_grounded = True
                    if coll.right == bot_rect.right:
                        sprite.is_right_toe_grounded = True
                    if sprite.is_left_toe_grounded and sprite.is_right_toe_grounded:
                        break
                
            if len(self.rect_collide(left_rect, candidates)) > 0:
                sprite.is_left_walled = True 
            if len(self.rect_collide(right_rect, candidates)) > 0:
                sprite.is_right_walled = True
        for sprite in movables: # solving movable-movable collisions
            colliding_with = [x for x in movables if self.really_intersects(sprite.rect, x.rect, self.thresh) and sprite is not x]
            for other in colliding_with:
                if other != sprite:
                    dir = self.intersect_dir(other.rect, sprite.rect, 0.2)
                    sprite.collided_with(other, dir)
        
    def solve_pushout_collision(self, unmovable, movable):
        assert unmovable.is_pushable == False and movable.is_pushable == True
        v_box = movable.rect.copy()
        v_box.inflate_ip(-v_box.width * self.thresh, 0)
        
        intersect = self.rect_intersect(unmovable.rect, v_box)  # vertical correction
        if intersect != None:
            if intersect.bottom == v_box.bottom:    # collision from bottom
                movable.rect.move_ip(0, -intersect.height)
                if movable.vy() > 0:
                    movable.set_vy(0)
                if movable.rf_parent != None:
                    movable.rf_parent.remove_from_rf(movable)
                unmovable.add_to_rf(movable)
                movable.collided_with(unmovable, "BOTTOM")
                unmovable.collided_with(movable, "TOP")
            elif intersect.top == v_box.top:        # collision from top
                movable.rect.move_ip(0, intersect.height)
                if movable.vy() < 0:
                    movable.set_vy(0)
                movable.collided_with(unmovable, "TOP")
                unmovable.collided_with(movable, "BOTTOM")
                
        h_box = movable.rect.copy()
        h_box.inflate_ip(0, -h_box.height * self.thresh)

        intersect = self.rect_intersect(unmovable.rect, h_box)  # horizontal correction
        if intersect != None:
            if intersect.left == h_box.left:
                movable.rect.move_ip(intersect.width, 0)
                movable.set_vx(0)
                movable.set_ax(0)
                movable.collided_with(unmovable, "LEFT")
                unmovable.collided_with(movable, "RIGHT")
            elif intersect.right == h_box.right:
                movable.rect.move_ip(-intersect.width, 0)
                movable.set_vx(0)
                movable.set_ax(0)
                movable.collided_with(unmovable, "RIGHT")
                unmovable.collided_with(movable, "LEFT")
        
    def rect_intersect(self, r1, r2):
        if not r1.colliderect(r2):
            return None
        
        left  = max(r1.x, r2.x)
        right = min(r1.x + r1.width, r2.x + r2.width)
        top   = max(r1.y, r2.y)
        bot   = min(r1.y + r1.height, r2.y + r2.height)
        
        return pygame.Rect(left, top, right-left, bot-top)
        
    def intersect_dir(self, r1, r2, thresh):
        "determines the direction from which r1 collides with r2"
        if not self.really_intersects(r1, r2, thresh):
            return "NONE"
        
        h_box = self.h_box(r2, thresh)
        v_box = self.v_box(r2, thresh)
        
        h_intersection = self.rect_intersect(r1, h_box)
        v_intersection = self.rect_intersect(r1, v_box)
        
        if h_intersection != None and v_intersection != None:
            # Colliding on both the guide rectangles, choose the one with larger overlap
            if h_intersection.width < v_intersection.height:
                v_intersection = None
            else:
                h_intersection = None
        
        if h_intersection == None:
            if v_intersection.centery - v_box.centery > 0:
                return "BOTTOM"
            else:
                return "TOP"
        else:
            if h_intersection.centerx - h_box.centerx > 0:
                return "RIGHT"
            else:
                return "LEFT"
        
    def really_intersects(self, movable_rect, unmovable_rect, thresh):
        h_box = self.h_box(movable_rect, thresh)
        v_box = self.v_box(movable_rect, thresh)
        
        return self.rect_intersect(h_box, unmovable_rect) != None or self.rect_intersect(v_box, unmovable_rect) != None

    def rect_collide(self, rect, sprite_list):
        "Finds all the sprites in Group (or list) spritegroup that collide with given rect. Returns a list of those sprites."
        return sorted([sprite for sprite in sprite_list if rect.colliderect(sprite.rect)])
        
    def h_box(self, rect, thresh):
        h_box = rect.copy()
        h_box.inflate_ip(0, -h_box.height * thresh)
        return h_box
        
    def v_box(self, rect, thresh):
        v_box = rect.copy()
        v_box.inflate_ip(-v_box.width * thresh, 0)
        return v_box
        
        
class ReferenceFrameFixer:
    def __init__(self):
        pass
        
    def solve_rfs(self, group):
        to_delete = sets.Set()
        for box in group:
            to_delete.clear()
            for kid in box.rf_children:
                if not kid.is_still_rf_child_of(box):
                    to_delete.add(kid)
            for kid in to_delete:
                box.remove_from_rf(kid)
        
        
class Path:
    def __init__(self, x_expression, y_expression, integral=True):
        self.t = 0;
        self.x_fun = x_expression
        self.y_fun = y_expression
        self.integral=integral
        
    def get_xy(self):
        x = self.x_fun(self.t)
        y = self.y_fun(self.t)
        if self.integral:
            x = int(x + 0.5) # rounding
            y = int(y + 0.5)
        return (x,y)
        
    def step(self, dt):
        self.t += dt

        
class PointPath(Path):  
    def __init__(self, x_points, y_points, speed=3):
        self.x_points = x_points
        self.y_points = y_points
        self.speed = speed
        if len(self.x_points) < 2 or len(self.y_points) < 2 or len(self.x_points) != len(self.y_points):
            raise ValueError("Path given arrays of invalid lengths: x_points="+str(len(self.x_points))+", y_points="+str(len(self.y_points)))
        self.dest_index = 1
        
        Path.__init__(self, self.get_spline_funct(self.x_points[0],self.x_points[1]), self.get_spline_funct(self.y_points[0],self.y_points[1]))
        
        self.at_end_of_spline = False
        
    def get_xy(self):
        if self.at_end_of_spline:
            return (self.x_points[self.dest_index], self.y_points[self.dest_index])
        else:
            return Path.get_xy(self)
            
    def step(self, dt):
        if self.at_end_of_spline:
            #time to move to next spline
            self.t = 0
            self.dest_index = (self.dest_index + 1) % len(self.x_points)
            
            self.x_fun = self.get_spline_funct(self.x_points[self.dest_index-1], self.x_points[self.dest_index])
            self.y_fun = self.get_spline_funct(self.y_points[self.dest_index-1], self.y_points[self.dest_index])
            self.at_end_of_spline = False
      
        self.t += dt
        inner = self.speed * 0.01 * self.t
        if inner > math.pi:
            self.at_end_of_spline = True
        
    def get_spline_funct(self, x1, x2):
        d = (x2 - x1)
        if d == 0:
            return equations.pythonify(str(x1))
        spline_string = "(+ "+str(x1)+" (* (/ "+str(d)+" 2) (- 1 (cos (* "+str(self.speed)+" 0.01 t)))))"
        return equations.pythonify(spline_string)

        
class Ghost(pygame.sprite.Sprite):
    def __init__(self, (x, y), color=(200, 128, 128)):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((24, 32))
        self.color = color
        self.repaint()
        self.rect = pygame.Rect(x, y, 24, 32)

    def repaint(self):
        self.image.fill(self.color)
        
    def is_ghost(self): return True
        
    def __str__(self):
        return "Ghost"+str(self.get_xy()) 
