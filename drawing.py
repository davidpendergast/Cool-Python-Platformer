import pygame 
import sets
import blocks
import utilities

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
        entity_list = self._filter_onscreen_entities(screen, entity_list, 30)
        paths = []
        if self.settings.draw_3d():
            non_players = [x for x in entity_list if not (x.is_actor() and x.is_player)]
            self._draw_entities_3D(screen, non_players)
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
    
    def _draw_entities_3D(self, screen, entity_list):
        all_corners = [self._get_front_and_back_corners(screen, entity) for entity in entity_list]
        all_colors = [entity.color for entity in entity_list]
        convex_hulls = [self._convex_hull(corners) for corners in all_corners]
        
        for (color, hull) in zip(all_colors, convex_hulls):
            color = utilities.darker(color, 60)
            self._fill_transparent_poly(screen, color, hull, 128)
            
        for (color, corners) in zip(all_colors, all_corners):
            front_corners = corners[0:4]
            back_corners = corners[4:]
            back_color = utilities.darker(color, 40)
            side_color = utilities.darker(color, 20)
            pygame.draw.lines(screen, back_color, True, back_corners, 2)
            for (f, b) in zip(front_corners, back_corners):
                pygame.draw.line(screen, side_color, f, b, 2)
            pygame.draw.lines(screen, color, True, front_corners, 2)
            
        
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
