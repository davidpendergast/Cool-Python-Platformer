import pygame 
import sets 

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
        