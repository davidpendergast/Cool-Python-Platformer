import pygame 
import sets
import blocks
import utilities
import random

class Drawer:
    def __init__(self, settings):
        self.settings = settings
        self.camera_pos = (0,0)
        self.grid_spacing = 32
        self.grid_color = (50,50,50)
    
    def draw_level(self, screen, level, entity_list=None, draw_background=True):    
        if draw_background:
            background_color = level.background_color
            background_color = self.update_background_color(background_color)
            screen.fill(background_color)
        
        if self.settings.show_grid():
            for x in range(0, screen.get_width() // self.grid_spacing+1):
                draw_x = x*self.grid_spacing - self.camera_pos[0]%self.grid_spacing
                pygame.draw.line(screen,self.grid_color,(draw_x, 0), (draw_x, screen.get_height()))
            for y in range(0, screen.get_height() // self.grid_spacing+1):
                draw_y = y*self.grid_spacing - self.camera_pos[1]%self.grid_spacing
                pygame.draw.line(screen,self.grid_color,(0, draw_y), (screen.get_width(), draw_y))
        
        if entity_list == None:
            entity_list = level.entity_list
        
        self.draw_entities(screen, entity_list)  
        
        if self.settings.show_spawns():
            self.draw_entities(screen, level.spawn_list)
        
        if self.settings.show_paths():
            for entity in entity_list:
                if entity.is_moving_block():
                    self.draw_path(screen, entity.get_path(), entity.xy_initial(), (255,255,0))      
            
    def draw_entities(self, screen, entity_list):
        entity_list = self._filter_onscreen_entities(screen, entity_list, 50)
        paths = []
        if self.settings.draw_3d():
            non_players = [x for x in entity_list if not (x.is_actor() and x.is_player)]
            random.shuffle(non_players)
            self._draw_entities_3D_2(screen, non_players)
            for entity in entity_list:
                if entity.is_actor() and entity.is_player:
                    self._decorate_sprite(entity)
                    self._draw_entity_2D(screen, entity)
        else:
            for entity in entity_list:
                self._decorate_sprite(entity)
                self._draw_entity_2D(screen, entity)
    
    def _decorate_sprite(self, entity):
        if entity.is_ghost():
                entity.image.set_alpha(128)
        elif entity.is_actor():
            self.draw_collision_indicators(entity)
    
    def _draw_entity_2D(self, screen, entity):
        screen.blit(entity.image, (entity.rect.x - self.camera_pos[0], entity.rect.y - self.camera_pos[1]))
            
    def _draw_entities_3D_2(self, screen, entity_list):
        entity_list.sort(key=lambda x: x.width()*x.height())
        entity_list.sort(key=lambda x: x.get_update_priority())
        all_rects = [_Rect.from_entity(x) for x in entity_list]
        #print "input = "+str(all_rects)
        disjoint_rects = []
        for i in range(0, len(all_rects)):
            r = all_rects[i]
            sub = r.subtract_all(all_rects[i+1:])
            disjoint_rects.extend(sub)
        
        c = (screen.get_width() / 2 + self.camera_pos[0], screen.get_height() / 2 + self.camera_pos[1])
        #self._color_by_category(disjoint_rects, c)
        sorter = lambda r1, r2: r1.overlapped_by_in_3D(r2, c)
        
        
        blocked_by = {x:sets.Set() for x in disjoint_rects} # blocked_by[n] = list of rects n prevents from being drawn
        blocking = {x:sets.Set() for x in disjoint_rects}   # blocking[n] = list of rects preventing n from being drawn
        unblocked = sets.Set(disjoint_rects)
        for r1 in disjoint_rects:
            for r2 in disjoint_rects: 
                if r1 is not r2 and r2.overlapped_by_in_3D(r1, c):
                    if r2 in blocking[r1]:
                        print "Cycle detected!!! "+ str(r1) + "-><-" + str(r2)
                    blocking[r2].add(r1)
                    blocked_by[r1].add(r2)
                    if r2 in unblocked:
                        unblocked.remove(r2)
        
        # Kahn's Algorithm for sorting a graph topologically
        L = []                  # result sorted list
        Adj = blocked_by        # adjacency lookup
        rev_Adj = blocking      # reverse adjacency lookup
        S = unblocked           # nodes with no incoming edges
        
        while len(S) > 0:
            n = S.pop()
            del rev_Adj[n]
            L.append(n)
            for node in Adj[n]:
                rev_Adj[node].remove(n)
                if len(rev_Adj[node]) == 0:
                    S.add(node)
                    
        if len(rev_Adj) > 0:
            print "Cycles in adjacency list!!!"
            print "c = "+str(c)
            print str(rev_Adj)

        L.reverse()
        self._draw_rects_3D(screen, L)
        
    
    def _draw_rects_3D(self, screen, rect_list):
        fronts_and_backs = [self._get_front_and_back_corners_2(screen, r) for r in rect_list]
        convex_hulls = [self._convex_hull(corners) for corners in fronts_and_backs]
        all_colors = [x.color for x in rect_list]
        
        for (color, corners, hull) in zip(all_colors, fronts_and_backs, convex_hulls):
            fill_color = utilities.darker(color, 60)
            self._fill_transparent_poly(screen, fill_color, hull, 128)
            
            front_corners = corners[0:4]
            back_corners = corners[4:]
            back_color = utilities.darker(color, 40)
            side_color = utilities.darker(color, 20)
            pygame.draw.lines(screen, back_color, True, back_corners, 2)
            for (f, b) in zip(front_corners, back_corners):
                pygame.draw.line(screen, side_color, f, b, 2)
            pygame.draw.lines(screen, color, True, front_corners, 2)
            
        # for (color, corners) in zip(all_colors, fronts_and_backs):
            # front_corners = corners[0:4]
            # back_corners = corners[4:]
            # back_color = utilities.darker(color, 40)
            # side_color = utilities.darker(color, 20)
            # pygame.draw.lines(screen, back_color, True, back_corners, 2)
            # for (f, b) in zip(front_corners, back_corners):
                # pygame.draw.line(screen, side_color, f, b, 2)
            # pygame.draw.lines(screen, color, True, front_corners, 2)
    
            
    def _color_by_category(self, rect_list, c):
        #   3  7  2
        #
        #   5  8  4
        #
        #   1  6  0
        colors = [
            (200,0,0),  #0
            (200,0,0),  #1 
            (0,0,200),  #2 
            (0,0,200),  #3 
            (0,200,0),  #4 
            (0,200,0),  #5 
            (160,0,0),  #6 
            (0,0,160),  #7 
            (255,255,255)   #8
        ]
        for rect in rect_list:
            rect.color = colors[rect._category(c)]

    def _fill_transparent_poly(self, screen, color, pointslist, alpha):
        pygame.draw.polygon(screen, color, pointslist, 0)
        # todo - make this work
        # s = pygame.Surface((screen.get_width(), screen.get_height()))
        # s.set_alpha(alpha)
        # pygame.draw.polygon(s, color, pointslist, 0)
        # screen.blit(s, (0,0))
        
    def _get_front_and_back_corners(self, screen, entity):
        depth = 0.05
        if entity.is_finish_block() or entity.is_spawn_point():
            depth = 0.02
            
        center = (screen.get_width() / 2, screen.get_height() / 2)
        cam = self.camera_pos
        corners = [
            (entity.x() - cam[0], entity.y() - cam[1]),
            (entity.x() + entity.width() - cam[0] - 1, entity.y() - cam[1]),
            (entity.x() + entity.width() - cam[0] - 1, entity.y() + entity.height() - cam[1] - 1),
            (entity.x() - cam[0], entity.y() + entity.height() - cam[1] - 1)
        ]
        
        back_corners = []
        for corner in corners:
            to_center = (center[0] - corner[0], center[1] - corner[1])
            back_corner = (int(corner[0] + depth*to_center[0]), int(corner[1] + depth*to_center[1]))
            back_corners.append(back_corner)
        
        return corners + back_corners
        
    def _get_front_and_back_corners_2(self, screen, rect):
        center = (screen.get_width() / 2, screen.get_height() / 2)
        cam = self.camera_pos
        corners = [
            (rect.x - cam[0], rect.y - cam[1]),
            (rect.x2 - cam[0] - 1, rect.y - cam[1]),
            (rect.x2 - cam[0] - 1, rect.y2 - cam[1] - 1),
            (rect.x - cam[0], rect.y2 - cam[1] - 1)
        ]
        
        back_corners = []
        for corner in corners:
            to_center = (center[0] - corner[0], center[1] - corner[1])
            back_corner = (int(corner[0] + rect.depth*to_center[0]), int(corner[1] + rect.depth*to_center[1]))
            back_corners.append(back_corner)
        
        return corners + back_corners
        
    def _draw_entity_THREE_DEE(self, screen, entity):
        face_color = entity.color
        side_color = utilities.darker(face_color, 20)
        bottom_color = utilities.darker(side_color, 20)
        top_color = utilities.lighter(face_color, 20)
 
        convex_hull = self._convex_hull(back_corners + corners)

        fill_color = utilities.darker(bottom_color, 30)
        pygame.draw.polygon(screen, fill_color, convex_hull, 0)
        
        pygame.draw.lines(screen, bottom_color, True, back_corners, 2)
        for (c , back_c) in zip(corners, back_corners):
            pygame.draw.line(screen, side_color, c, back_c, 2)
        pygame.draw.lines(screen, face_color, True, corners, 2)
                
    def _convex_hull(self, points):
        min_x = [points[0]]
        max_x = [points[0]]
        min_y = [points[0]]
        max_y = [points[0]]
        for point in points:
            if point[0] == min_x[0][0]: min_x.append(point)
            elif point[0] < min_x[0][0]: min_x = [point]
            if point[0] == max_x[0][0]: max_x.append(point)
            elif point[0] > max_x[0][0]: max_x = [point]
            if point[1] == min_y[0][1]: min_y.append(point)
            elif point[1] < min_y[0][1]: min_y = [point]
            if point[1] == max_y[0][1]: max_y.append(point)
            elif point[1] > max_y[0][1]: max_y = [point]
        min_x.sort(key=lambda p: -p[1])
        min_y.sort(key=lambda p: p[0])
        max_x.sort(key=lambda p: p[1])
        max_y.sort(key=lambda p: -p[0])
        dupes = sets.Set([])
        res = []
        for point in min_x + min_y + max_x + max_y:
            if point in dupes:
                continue
            else:
                res.append(point)
                dupes.add(point)
                
        return res
        
    def _filter_onscreen_entities(self, screen, entity_list, icing=0):
        return [x for x in entity_list if self._is_onscreen(screen, x, icing)]
    
    def _is_onscreen(self, screen, entity, icing):
        screen_x = self.camera_pos[0] - icing
        screen_y = self.camera_pos[1] - icing
        screen_w = screen.get_width() + 2*icing 
        screen_h = screen.get_height() + 2*icing
        
        return not (screen_x + screen_w <= entity.x() or 
                screen_y + screen_h <= entity.y() or
                screen_x >= entity.x() + entity.width() or
                screen_y >= entity.y() + entity.height())
    
    def draw_path(self, screen, path, offset, color, start_t=0, end_t=360, step=30):
        offset = self._sub(self.camera_pos, offset)
        if path.is_funct_path():
            times = range(start_t, end_t, step)
            points = [self._sub(path.get_xy(t), offset) for t in times]
            closed = False
        elif path.is_point_path():
            points = [self._sub(xy, offset) for xy in zip(path.x_points, path.y_points)]
            closed = True
            
        pygame.draw.lines(screen, color, closed, points, 2)
    
    def _sub(self, tuple1, tuple2):
        return tuple([x - y for (x,y) in zip(tuple1, tuple2)])
    def _add(self, tuple1, tuple2):
        return tuple([x + y for (x,y) in zip(tuple1, tuple2)])
        
    def update_camera(self, box, screen_width, screen_height):
        rect = box.rect
        self.camera_pos = (rect.x + rect.width/2 - screen_width/2, rect.y + rect.height/2 - screen_height/2)
    
    def screen_to_game_position(self, screen_pos, snap_to_grid=False):
        x = screen_pos[0] + self.camera_pos[0]
        y = screen_pos[1] + self.camera_pos[1]
        
        if snap_to_grid:
            x = x - (x % self.grid_spacing)
            y = y - (y % self.grid_spacing)
            
        return (x, y)
    
    def move_camera(self, dx, dy):
        self.camera_pos = (self.camera_pos[0] + dx, self.camera_pos[1] + dy) 
    
    def update_background_color(self, background_color):
        if self.camera_pos[1] < 512:
            return background_color
        else:
            redness = (self.camera_pos[1] - 512) / (2048.0 - 512.0)
            max_red = 192
            ## want r,g,b -> 192,0,0 as y -> 2048
            return (
                int(background_color[0] + redness*(max_red - background_color[0])),
                int(background_color[1] * (1 - redness)),
                int(background_color[2] * (1 - redness))
            )  
            
    def draw_collision_indicators(self, actor):
        actor.image.fill(actor.color) #reseting actor
        if actor.is_grounded:
            actor.image.fill((255,255,0), (0, actor.rect.height - 4, actor.rect.width, 4))
        if actor.is_left_walled:
            actor.image.fill((255,255,255), (0, 0, 4, actor.rect.height))
        if actor.is_right_walled:
            actor.image.fill((255,255,255), (actor.rect.width-4, 0, 4, actor.rect.height))
        if actor.jumps > 0:
            actor.image.fill((50,255,50), (actor.rect.width/2-4, actor.rect.height/2-4, 8, 8))
        if actor.is_left_toe_grounded:
            actor.image.fill((255,255,125), (0,actor.rect.height-8,8,8))
        if actor.is_right_toe_grounded:
            actor.image.fill((255,255,125), (actor.rect.width-8,actor.rect.height-8,8,8))
            
class _Rect:
    def __init__(self, x, y, w, h, color=(0,0,0), depth=0.05):
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)
        self.color = color
        self.depth = depth
        
        self.x2 = x + w
        self.y2 = y + h
        self.top_left = (x, y)
        self.top_right = (x + w, y)
        self.bottom_left = (x, y + h)
        self.bottom_right = (x + w, y + h)
        self.center = (x + w/2, y + h/2)
    
    @staticmethod
    def from_points(p1, p2, color=(0,0,0), depth=0.05):
        return _Rect(  min(p1[0], p2[0]), 
                min(p1[1], p2[1]), 
                abs(p2[0] - p1[0]), 
                abs(p2[1] - p1[1]), 
                color, 
                depth)
    
    @staticmethod
    def from_entity(entity):
        depth = 0.02 if entity.is_spawn_point() or entity.is_finish_block() or entity.is_ghost() else .1 # 0.05
        return _Rect(entity.x(), entity.y(), entity.width(), entity.height(), entity.color, depth)
                
    def corners(self):
        return [self.top_left, self.top_right, self.bottom_right, self.bottom_left]
        
    def subtract(self, r2):
        if not self.intersects(r2):
            return [self]
        
        results = [self]
        corners = r2.corners()
        if self.contains_any(corners, inclusive=True):
            for point in r2.corners():
                new_rects = []
                for rect in results:
                    quads = rect.quad_divide(point)
                    # print str(quads)
                    new_rects.extend(quads)
                results = new_rects
        else:
            # four possible rectangles in this case
            # at most two are non-empty
            results = [
                _Rect.from_points((self.x, self.y), (r2.x, self.y2), self.color, self.depth),
                _Rect.from_points((r2.x2, self.y), (self.x2, self.y2), self.color, self.depth),
                _Rect.from_points((self.x, self.y), (self.x2, r2.y), self.color, self.depth),
                _Rect.from_points((self.x, r2.y2), (self.x2, self.y2), self.color, self.depth)
            ]
            
            
        
        return [x for x in results if not x.intersects(r2)]
        
    def subtract_all(self, rect_list):
        result = [self]
        for i in range(0, len(rect_list)):
            r = rect_list[i]
            sub = self.subtract(r)
            if len(sub) == 0:
                return []
            elif self not in sub:
                result = []
                for sub_rect in sub:
                    result.extend(sub_rect.subtract_all(rect_list[i:]))
                return result
        return result    
        
    def intersects(self, r2):
        return self.horz_overlaps(r2) and self.vert_overlaps(r2)
                
    def horz_overlaps(self, r2):
        return not (r2.x >= self.x2 or self.x >= r2.x2)
        
    def vert_overlaps(self, r2):
        return not (r2.y >= self.y2 or self.y >= r2.y2)
        
    def _btw(self, x, min, max):
        return min < x and x < max
        
    def quad_divide(self, point):
        if not self.contains(point, inclusive=True) or (point[0] == self.x and point[1] == self.y):
            return [self]
        else: 
            quads = [
                _Rect.from_points(self.top_left, point, self.color, self.depth),
                _Rect.from_points(self.top_right, point, self.color, self.depth),
                _Rect.from_points(self.bottom_left, point, self.color, self.depth),
                _Rect.from_points(self.bottom_right, point, self.color, self.depth)
            ]
            return [x for x in quads if not x.is_empty()]
            
    def contains(self, point, inclusive=False):
        border = 1 if inclusive else 0
        return (self.x <= point[0] and 
                self.y <= point[1] and 
                self.x + self.w + border > point[0] and 
                self.y + self.h + border > point[1])
                
    def contains_any(self, points_list, inclusive=False):
        for point in points_list:
            if self.contains(point, inclusive):
                return True
        return False
        
    def is_empty(self):
        return self.w == 0 or self.h == 0
    
    def __str__(self):
        return "["+str(self.x)+", "+str(self.y)+", "+str(self.w)+", "+str(self.h)+"]"
    def __repr__(self):
        return str(self)
    def __eq__(self, r2):
        return (self.x == r2.x and self.x2 == r2.x2
                and self.y == r2.y and self.y2 == r2.y2)
                
    def overlapped_by_in_3D(self, r2, c):
        quads1 = self.quadrants(c)
        quads2 = r2.quadrants(c)
        
        if len(quads1 & quads2) == 0:
            return False
     
        h_overlap = self.horz_overlaps(r2)
        v_overlap = self.vert_overlaps(r2)
        
        horz1 = self._horz_dist_to(c)
        horz2 = r2._horz_dist_to(c)
        vert1 = self._vert_dist_to(c)
        vert2 = r2._vert_dist_to(c)
        
        if v_overlap:
            return horz1 > horz2
        elif h_overlap:
            return vert1 > vert2
        else:
            return False # min(horz1, vert1) > min(horz2, vert2)
        
    def quadrants(self, c):
        quads = sets.Set()
        if self.x < c[0] and self.y < c[1]:
            quads.add(1)
        if self.x2 > c[0] and self.y < c[1]:
            quads.add(2)
        if self.x2 > c[0] and self.y2 > c[1]:
            quads.add(3)
        if self.x < c[0] and self.y2 > c[1]:
            quads.add(4)
        return quads
        
        
        
    def _manhatten_dist_to(self, point):
        if self.contains(point):
            return 0
        return min(
            abs(self.x - point[0]),
            abs(self.y - point[1]),
            abs(self.x2 - point[0]),
            abs(self.y2 - point[1]),
        )
        
    def _horz_dist_to(self, point):
        if self._btw(point[0], self.x, self.x2):
            return 0
        return min(abs(self.x - point[0]), abs(self.x2 - point[0]))
        
    def _vert_dist_to(self, point):
        if self._btw(point[1], self.y, self.y2):
            return 0
        return min(abs(self.y - point[1]), abs(self.y2 - point[1]))
          
    
    def _category(self, c):   
        #   3  7  2
        #
        #   5  8  4
        #
        #   1  6  0
        arr = [3, 7, 2, 5, 8, 4, 1, 6, 0]
        
        if self._btw(c[0], self.x, self.x2): col = 1
        elif self.x2 < c[0]: col = 0
        else: col = 2 
        
        if self._btw(c[1], self.y, self.y2): row = 1
        elif self.y2 < c[1]: row = 0
        else: row = 2 
        
        return arr[row*3 + col]
        
    def __hash__(self):
        return str(self).__hash__()
            
  
if __name__ == "__main__":
    r1 = _Rect(0,0,10,10)
    r2 = _Rect(0,0,5,5)
    r3 = _Rect.from_points((5,0), (10,10))
    #print str(r3)
    #print str(r1) +" - "+ str(r2) +" = "+ str(r1.subtract(r2))  

    r1 = _Rect(-32, 192, 384, 544)
    rects =  [_Rect(-512, -224, 480, 960), _Rect(352, 192, 32, 64)]
    #print str(r1) +" - "+ str(rects) +" = "+ str(r1.subtract_all(rects))
    #print str(r1) +" - "+ str(rects[0]) +" = "+ str(r1.subtract(rects[0]))
    #print str(r1) +" - "+ str(rects[1]) +" = "+ str(r1.subtract(rects[1]))

    c = (852, -1095)
    r1 = _Rect(1152, -1312, 64, 32)
    r2 = _Rect(1208, -1280, 8, 64)
    r3 = _Rect(928, -1632, 224, 192)
    
    # crap this is a legit cycle...
    c = (1074, -604)
    r1 = _Rect(672, -832, 128, 288)
    r2 = _Rect(1024, -864, 448, 64)
    r3 = _Rect(1260, -608, 8, 640)
    r4 = _Rect(672, -544, 480, 256)
    print "r1 -> r2: "+str(r1.overlapped_by_in_3D(r2, c))
    print "r2 -> r3: "+str(r2.overlapped_by_in_3D(r3, c))
    print "r3 -> r4: "+str(r3.overlapped_by_in_3D(r4, c))
    print "r4 -> r1: "+str(r4.overlapped_by_in_3D(r1, c))
    

    print str(r1.subtract(r2))
