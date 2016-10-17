import pygame, blocks

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
        for sprite in entity_list:
            if sprite.is_ghost():
                sprite.image.set_alpha(128)
            elif sprite.is_actor():
                self.draw_collision_indicators(sprite)
            
            screen.blit(sprite.image, (sprite.rect.x - self.camera_pos[0], sprite.rect.y - self.camera_pos[1]))
    
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
