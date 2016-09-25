import pygame
import sys
import json

import phys_objects
import drawing
import levels
import collisions
from options import HardSettings
from utilities import Utils

class GameState:
    def pre_event_update(self):
        pass
    def handle_event(self, event):
        pass
    def update(self, dt):
        pass
    def draw(self, screen):
        pass
        
class PlayingState(GameState):
    def __init__(self, settings):
        self.settings = settings
        self.player = phys_objects.Actor(24, 32, (128, 128, 255))
        self.player.is_player = True
        
        self.level_num = 0
        self.death_count = 0
        
        self.total_time = 0
        self.level_time = 0 
        
        self._level_manager = levels.LevelManager(self.settings)
        
        self.pusher = collisions.CollisionFixer()
        self.rf_fixer = collisions.ReferenceFrameFixer()
        self.drawer = drawing.Drawer()
        
        self.keys = {'left':False, 'right':False, 'jump':False}
        self.mouse_down_pos = None
        self.font = pygame.font.Font(pygame.font.match_font("consolas", bold=True), 24)
        
        self.full_reset() # starts game from scratch
        
    def get_entities(self):
        return self._level_manager.current_level.entity_list
        
    def pre_event_update(self):
        if self.player.is_crushed == True:
            self.player.is_alive = False
        if self.player.is_alive == False and not self.settings.invincible_mode():
            self.player.is_alive = True
            self.death_count += 1
            self.reset_level()
        if self.player.finished_level:
            self.next_level(True)
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                self.keys['left'] = True
            elif event.key == pygame.K_d:
                self.keys['right'] = True
            elif event.key == pygame.K_w:
                self.keys['jump'] = True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_r:
                self.death_count += 1
                self.reset_level()
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.full_reset()
                return True
            elif event.key == pygame.K_g:
                self.drawer.show_grid = not self.drawer.show_grid
            elif event.key == pygame.K_k and self.settings.dev_mode():
                self.settings.set_invincible_mode(not self.settings.invincible_mode())
            elif event.key == pygame.K_f and self.settings.dev_mode():
                self.settings.set_frozen_mode(not self.settings.frozen_mode())
            elif event.key == pygame.K_RIGHT and self.settings.dev_mode():
                self.next_level()
                return True
            elif event.key == pygame.K_LEFT and self.settings.dev_mode():
                self.prev_level()
                return True
            elif event.key == pygame.K_DOWN and self.settings.dev_mode():
                self.reset_level(False)
                return True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                self.keys['left'] = False
            elif event.key == pygame.K_d:
                self.keys['right'] = False
            elif event.key == pygame.K_w:
                self.keys['jump'] = False
        elif event.type == pygame.MOUSEBUTTONDOWN and self.settings.dev_mode():
            x = event.pos[0]+self.drawer.camera_pos[0]
            y = event.pos[1]+self.drawer.camera_pos[1]
            grid_size = self.drawer.grid_spacing
            grid_x = x - (x % grid_size)
            grid_y = y - (y % grid_size)
            self.mouse_down_pos = (x,y)
            if event.button == 1:
                print "Mouse Click at: ("+str(x)+", "+str(y)+") ["+str(grid_x)+", "+str(grid_y)+"]"
            elif event.button == 3:
                print "{\"type\":\"finish\", \"x\":\""+str(grid_x + grid_size/4) +"\", \"y\":\""+str(grid_y + grid_size/4)+"\", \"width\":\""+str(grid_size/2)+"\", \"height\":\""+str(grid_size/2)+"\"}"
            
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.settings.dev_mode():
            x = event.pos[0]+self.drawer.camera_pos[0]
            y = event.pos[1]+self.drawer.camera_pos[1]
            grid_x = x - (x % self.drawer.grid_spacing)
            grid_y = y - (y % self.drawer.grid_spacing)
            if self.mouse_down_pos != None:
                grid_down_x = self.mouse_down_pos[0] - (self.mouse_down_pos[0] % self.drawer.grid_spacing)
                grid_down_y = self.mouse_down_pos[1] - (self.mouse_down_pos[1] % self.drawer.grid_spacing)
                if grid_x != grid_down_x or grid_y != grid_down_y:
                    #mouse has been dragged across more than one grid square.
                    print "Mouse Dragged to form rectangle:["+str(grid_down_x)+", "+str(grid_down_y)+", "+str(grid_x - grid_down_x)+", "+str(grid_y - grid_down_y)+"]"
                    print "{\"type\":\"normal\", \"x\":\""+str(grid_down_x)+"\", \"y\":\""+str(grid_down_y)+"\", \"width\":\""+str(grid_x - grid_down_x)+"\", \"height\":\""+str(grid_y - grid_down_y)+"\"}"
                    print "\"x_path\":\"(+ "+str((grid_x+grid_down_x)/2)+" (* "+str((grid_x-grid_down_x)/2)+" (cos (* 0.02 t))))\""
                    print "\"y_path\":\"(+ "+str((grid_y+grid_down_y)/2)+" (* "+str((grid_y-grid_down_y)/2)+" (sin (* 0.02 t))))\""

        if self.keys['jump']:
            self.player.jump_action()
            self.keys['jump'] = False
    
    def update(self, dt):
        self.add_time(dt)
        
        if bool(self.keys['left']) ^ bool(self.keys['right']):
            if self.keys['left']: 
                self.player.move_action(-1)
            elif self.keys['right']: 
                self.player.move_action(1)
        else:
            self.player.apply_friction(dt)
        
        self.player.update(dt)
        
        if self.settings.frozen_mode():
            dt = 0
        
        for item in self.get_entities():
            if item is not self.player:
                item.update(dt)
        
        self.pusher.solve_collisions(self._level_manager.current_level.entity_list)
        self.rf_fixer.solve_rfs(self._level_manager.current_level.entity_list)
        
        self._level_manager.current_level.bring_out_yer_dead()
    
    def draw(self, screen):
        self.drawer.update_camera(self.player, screen.get_width(), screen.get_height())
        self.drawer.draw(screen, self.get_entities())
        self.draw_gui(screen)
     
    def add_time(self, t):
        self.total_time += 1
        self.level_time += 1
      
    def reset_level(self, reset_player=True):
        x = self.player.x()
        y = self.player.y()
        
        self.player.reset()
        self._level_manager.load_level(self.level_num, self.player)
        
        if not reset_player:
            self.player.set_xy(x,y)
    
    def full_reset(self):
        self.player.reset()
        self.level_num = 0
        self.total_time = 0
        self.level_time = 0
        self.death_count = 0
        self._level_manager.load_level(0, self.player)
        print "\nGame Start!"
    
    def next_level(self, update_highscore=False):
        if update_highscore:
            self._level_manager.update_level_highscore(self.level_num, self.level_time)
            
        if self.level_num == self._level_manager.get_num_levels() - 1:
            self.full_reset()
        else:   
            self.level_num += 1
            self.level_time = 0
            self.player.reset()
            self._level_manager.load_level(self.level_num, self.player)
      
    def prev_level(self):
        "only used in dev mode"
        self.level_num = (self.level_num - 1) % self._level_manager.get_num_levels()
        self.player.reset()
        self._level_manager.load_level(self.level_num, self.player)
    
    def draw_gui(self, screen):
        level_text = self.font.render("Level: "+str(self.level_num + 1), True, (255, 255, 255))
        level_title = self.font.render(str(self._level_manager.current_level.name), True, (255, 255, 255))
        death_text = self.font.render("Deaths: "+str(self.death_count), True, (255, 255, 255))
        text_height = level_text.get_height()
        
        best_total_time = self._level_manager.get_best_run_time()
        total_time_text_color = self.get_time_display_color(self.total_time, best_total_time, start_color=(255,255,255), end_color=(255,255,255))
        total_time_text = self.font.render("Total: " + Utils.format_time(self.total_time), True, total_time_text_color)
        
        best_level_time = self._level_manager.get_best_level_time(self.level_num)
        level_time_text_color = self.get_time_display_color(self.level_time, best_level_time)
        level_time_text = self.font.render("Level: "+Utils.format_time(self.level_time), True, level_time_text_color)
        
        screen.blit(level_text, (0, 0))
        screen.blit(level_title, (0, text_height))
        screen.blit(total_time_text, (screen.get_width()/2 - total_time_text.get_width()/2, 0))
        screen.blit(level_time_text, (screen.get_width()/2 - level_time_text.get_width()/2, text_height))
        screen.blit(death_text, (screen.get_width() - death_text.get_width(), 0))
        
        standard_width = HardSettings.standard_size()[0]
        standard_height = HardSettings.standard_size()[1]
        
        if screen.get_width() > standard_width or screen.get_height() > standard_height:
            xoffset = (screen.get_width() - standard_width) / 2
            yoffset = (screen.get_height() - standard_height) / 2
            pygame.draw.rect(screen,(255,0,0), pygame.Rect(xoffset,yoffset,standard_width,standard_height), 1)
            
    def get_time_display_color(self, current_time, best_time, start_color=(0, 255, 0), end_color=(255, 255, 100), fail_color=(255, 0, 0)):
        if best_time == None:
            return start_color
        elif current_time > best_time or best_time <= 0:
            return fail_color
        else:
            val = current_time/float(best_time)
            return (
                int(start_color[0] + val*(end_color[0]-start_color[0])),
                int(start_color[1] + val*(end_color[1]-start_color[1])), 
                int(start_color[2] + val*(end_color[2]-start_color[2]))
            )
           
       
class EditingState(GameState):
    pass
