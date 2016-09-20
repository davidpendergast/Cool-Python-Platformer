import pygame
import sys
import json

import phys_objects
import drawing
import levels

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
    def __init__(self):
        self.player = phys_objects.Actor(24, 32, (128, 128, 255))
        self.player.is_player = True
        
        self.level_num = 0
        self.death_count = 0
        
        self.total_time = 0
        self.level_time = 0
        
        with open("settings.json") as data_file:    
            data = json.load(data_file)
            self.DEV_MODE = data["dev_mode"]
            level_path_string = data["level_path"]     
        
        print "Using levels from "+level_path_string
        
        self._level_manager = levels.LevelManager(level_path_string)
        self._level_manager.load_level(0, self.player)
        
        self.pusher = phys_objects.CollisionFixer()
        self.rf_fixer = phys_objects.ReferenceFrameFixer()
        self.drawer = drawing.Drawer()
        
        self.keys = {'left':False, 'right':False, 'jump':False}
        self.mouse_down_pos = None
        
        self.invincible_mode = False
        self.frozen_mode = False
    
    def get_entities(self):
        return self._level_manager.current_level.entity_list
        
    def pre_event_update(self):
        if self.player.is_crushed == True:
            self.player.is_alive = False
        if self.player.is_alive == False and not self.invincible_mode:
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
            elif event.key == pygame.K_k and self.DEV_MODE:
                self.invincible_mode = not self.invincible_mode
            elif event.key == pygame.K_f and self.DEV_MODE:
                self.frozen_mode = not self.frozen_mode
            elif event.key == pygame.K_RIGHT and self.DEV_MODE:
                self.next_level()
                return True
            elif event.key == pygame.K_LEFT and self.DEV_MODE:
                self.prev_level()
                return True
            elif event.key == pygame.K_DOWN and self.DEV_MODE:
                self.reset_level(False)
                return True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                self.keys['left'] = False
            elif event.key == pygame.K_d:
                self.keys['right'] = False
            elif event.key == pygame.K_w:
                self.keys['jump'] = False
        elif event.type == pygame.MOUSEBUTTONDOWN and self.DEV_MODE:
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
            
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.DEV_MODE:
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
        
        if self.frozen_mode:
            dt = 0
        
        for item in self.get_entities():
            if item is not self.player:
                item.update(dt)
        
        self.pusher.solve_collisions(self._level_manager.current_level.entity_list)
        self.rf_fixer.solve_rfs(self._level_manager.current_level.entity_list)
    
    def draw(self, screen):
        self.drawer.update_camera(self.player, screen.get_width(), screen.get_height())
        # drawer.draw(screen, client.get_ghosts()) #### GHOSTS NOT BEING DRAWN ####
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
    
    def next_level(self, update_highscore=False):
        if update_highscore:
            self._level_manager.update_level_highscore(self.level_num, self.level_time)
            
        if self.level_num == self._level_manager.get_num_levels() - 1:
            print "Game Over!"
            
            # TEMPORARY - loop back to level 0
            self.level_num = 0
            self.level_time = 0
            self.total_time = 0
            self.player.reset()
            self._level_manager.load_level(self.level_num, self.player)
        else:   
            self.level_num += 1
            self.level_time = 0
            self.player.reset()
            self._level_manager.load_level(self.level_num, self.player)
      
    def prev_level(self):
        if self.level_num > 0:
            self.level_num += -1
        self.player.reset()
        self._level_manager.load_level(self.level_num, self.player)
    
    def draw_gui(self, screen):
        font = pygame.font.Font(None, 36)
        level_text = font.render("Level: "+str(self.level_num + 1), True, (255, 255, 255))
        level_title = font.render(str(self._level_manager.current_level.name), True, (255, 255, 255))
        death_text = font.render("Deaths: "+str(self.death_count), True, (255, 255, 255))
        text_height = level_text.get_height()
        
        time_text = font.render("Time: " + PlayingState.format_time_string(self.total_time), True, (255, 255, 255))
        screen.blit(level_text, (0, 0))
        screen.blit(level_title, (0, text_height))
        screen.blit(time_text, (screen.get_width()/2 - time_text.get_width()/2, 0))
        screen.blit(death_text, (screen.get_width() - death_text.get_width(), 0))
        
        if screen.get_width() > 640 or screen.get_height() > 480:
            pygame.draw.rect(screen,(255,0,0), pygame.Rect(100,100,640,480), 1)
      
    @staticmethod
    def format_time_string(time):
        if time == None:
            return None
        if time % 60 < 10:
            seconds = "0" + str(time % 60)
        else:
            seconds = str(time % 60)
        return str(time // 60) + ":" + seconds
        
    @staticmethod
    def unformat_time_string(time_string):
        "'34:56' -> 34*60 + 56"
        if time_string == None:
            return None
        split = time_string.split(":")
        if len(split) == 2:
            return int(split[0])*60 + int(split[1])
        else:
            raise ValueError("invalid time string to unformat: "+str(time_string))
       
class EditingState(GameState):
    pass
            
            
            
            
            
            