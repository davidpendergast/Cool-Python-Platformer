import pygame, phys_objects

class Drawer:
    def __init__(self):
        self.background_color = (0,0,0)
        self.camera_pos = (0,0)
        self.show_grid = False
        self.grid_spacing = 32
        self.grid_color = (50,50,50)
    
    def draw(self, screen, entity_list):
        self.update_background_color()
        screen.fill(self.background_color)
        if self.show_grid:
            for x in range(0, screen.get_width() // self.grid_spacing+1):
                draw_x = x*self.grid_spacing - self.camera_pos[0]%self.grid_spacing
                pygame.draw.line(screen,self.grid_color,(draw_x, 0), (draw_x, screen.get_height()))
            for y in range(0, screen.get_height() // self.grid_spacing+1):
                draw_y = y*self.grid_spacing - self.camera_pos[1]%self.grid_spacing
                pygame.draw.line(screen,self.grid_color,(0, draw_y), (screen.get_width(), draw_y))
        
        for sprite in entity_list:
            if sprite.is_ghost():
                sprite.image.set_alpha(128)
            elif sprite.is_actor():
                self.draw_collision_indicators(sprite)
            
            screen.blit(sprite.image, (sprite.rect.x - self.camera_pos[0], sprite.rect.y - self.camera_pos[1]))
    
    def update_camera(self, box, screen_width, screen_height):
        rect = box.rect
        self.camera_pos = (rect.x + rect.width/2 - screen_width/2, rect.y + rect.height/2 - screen_height/2)
    
    def move_camera(self, dx, dy):
        self.camera_pos = (self.camera_pos[0] + dx, self.camera_pos[1] + dy) 
    
    def update_background_color(self):
        if self.camera_pos[1] < 512:
            self.background_color = (0,0,0)
        else:
            self.background_color = (min(255*3/4, (self.camera_pos[1] - 512)//8),0,0)  
            
    def draw_collision_indicators(self, actor):
        actor.image.fill(actor.color) #reseting actor
        if actor.is_grounded:
            actor.image.fill((255,255,0), (0, actor.rect.height - 4, actor.rect.width, 4))
        if actor.is_left_walled:
            actor.image.fill((255,255,255), (0, 0, 4, actor.rect.height))
        if actor.is_right_walled:
            actor.image.fill((255,255,255), (actor.rect.width-4, 0, 4, actor.rect.height))
        if actor.jumps > 0:
            actor.image.fill((0,255,0), (actor.rect.width/2-4, actor.rect.height/2-4, 8, 8))
        if actor.is_left_toe_grounded:
            actor.image.fill((255,255,125), (0,actor.rect.height-8,8,8))
        if actor.is_right_toe_grounded:
            actor.image.fill((255,255,125), (actor.rect.width-8,actor.rect.height-8,8,8))
