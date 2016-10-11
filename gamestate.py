import pygame
import sys
import json
import os

import blocks, actors
import drawing
import levels
import collisions
from options import HardSettings
import utilities

class GameState:
    def __init__(self, settings):
        self.settings = settings
        self.state_manager = None # gets set when gamestate is added to a manager
    def pre_event_update(self):
        pass
    def handle_event(self, event):
        pass
    def update(self, dt):
        pass
    def draw(self, screen):
        pass
    def switching_to(self, prev_state_id):
        pass
    def switching_from(self, new_state_id):
        pass
        
class GameStateManager(GameState):
    # state identifiers
    MAIN_MENU_STATE = "menu_state"
    PLAYING_STATE = "playing_state"
    EDITING_STATE = "editing_state"
    GAME_OVER_STATE = "game_over_state"
    
    def __init__(self, settings):
        self.states = {
            GameStateManager.MAIN_MENU_STATE:None,
            GameStateManager.PLAYING_STATE:None,
            GameStateManager.EDITING_STATE:None,
            GameStateManager.GAME_OVER_STATE:None
        }
        self.settings = settings
        self.current_state_id = None
    
    def set_state(self, state_id, gamestate):
        gamestate.state_manager = self
        self.states[state_id] = gamestate
    
    def get_state(self, state_id):
        return self.states[state_id]
    
    def get_current_state(self):
        if self.current_state_id == None:
            return None
        else:
            return self.states[self.current_state_id]
    
    def set_current_state(self, state_id):
        if self.get_current_state() != None:
            self.get_current_state().switching_from(state_id)
        
        old_state_id = self.current_state_id
        self.current_state_id = state_id
        
        if self.get_current_state() != None:
            self.get_current_state().switching_to(old_state_id)
            
        utilities.log("GameState changed: "+str(old_state_id)+" -> "+str(state_id))
        utilities.log("Current state: "+str(self.get_current_state()))

    def pre_event_update(self):
        if self.get_current_state() != None:
            self.get_current_state().pre_event_update()
        
    def handle_event(self, event):
        if self.get_current_state() != None:
            self.get_current_state().handle_event(event)
        
    def update(self, dt):
        if self.get_current_state() != None:
            self.get_current_state().update(dt)
        
    def draw(self, screen):
        if self.get_current_state() != None:
            self.get_current_state().draw(screen)
        
class PlatformerInstance:
    "state that's shared between PlayingState and EditingState"
    def __init__(self, settings):
        self.settings = settings
        self.player = actors.Actor(24, 32, settings.get_color())
        self.player.is_player = True
        self.level_manager = levels.LevelManager(self.settings)
        self.drawer = drawing.Drawer()
        
        self.level_num = 0
        
    def get_entities(self):
        return self.current_level().entity_list
    def get_player(self):
        return self.player
    def current_level(self):
        return self.level_manager.current_level
    def get_level_num(self):
        return self.level_num
    def set_level_num(self, num):
        self.level_num = num
    def load_level(self, reset_ghost=True):
        self.level_manager.load_level(self.get_level_num(), self.get_player(), reset_ghost)
    
class InGameState(GameState):
    def __init__(self, settings, platformer_instance):
        GameState.__init__(self, settings)
        self.platformer_instance = platformer_instance
        self.keys = {
            'left':False, 
            'right':False, 
            'jump':False,
            'up':False,
            'down':False,
            'shift':False,
            'ctrl':False
        }
        self.mouse_down_pos = None
        self.font = pygame.font.Font(pygame.font.match_font("consolas", bold=True), 24)
    def get_entities(self):
        return self.platformer_instance.get_entities()   
    def get_level_manager(self):
        return self.platformer_instance.level_manager
    def get_level_num(self):
        return self.platformer_instance.get_level_num()
    def get_player(self):
        return self.platformer_instance.get_player()
    def get_current_level(self):
        return self.platformer_instance.current_level()
    def get_drawer(self):
        return self.platformer_instance.drawer
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                self.keys['left'] = True
            elif event.key == pygame.K_d:
                self.keys['right'] = True
            elif event.key == pygame.K_w:
                self.keys['jump'] = True
                self.keys['up'] = True
            elif event.key == pygame.K_g:
                self.get_drawer().show_grid = not self.get_drawer().show_grid
            elif event.key == pygame.K_f and self.settings.dev_mode():
                self.settings.set_frozen_mode(not self.settings.frozen_mode())
            elif event.key == pygame.K_w:
                self.keys['up'] = True
            elif event.key == pygame.K_s:
                self.keys['down'] = True
            elif event.key == pygame.K_RCTRL or event.key == pygame.K_LCTRL:
                self.keys['ctrl'] = True
            elif event.key == pygame.K_RSHIFT or event.key == pygame.K_LSHIFT:
                self.keys['shift'] = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                self.keys['left'] = False
            elif event.key == pygame.K_d:
                self.keys['right'] = False
            elif event.key == pygame.K_w:
                self.keys['jump'] = False
                self.keys['up'] = False
            elif event.key == pygame.K_s:
                self.keys['down'] = False
            elif event.key == pygame.K_RCTRL or event.key == pygame.K_LCTRL:
                self.keys['ctrl'] = False
            elif event.key == pygame.K_RSHIFT or event.key == pygame.K_LSHIFT:
                self.keys['shift'] = False
    
    def switching_to(self, prev_state_id):
        for key in self.keys:
            self.keys[key] = False
        
class PlayingState(InGameState):
    def __init__(self, settings, platformer_instance):
        InGameState.__init__(self, settings, platformer_instance)
        
        self.ghost_recorder = actors.GhostRecorder(self.get_player())
        self.death_count = 0
        
        self.total_time = 0
        self.level_time = 0 
        
        self.pusher = collisions.CollisionFixer()
        self.rf_fixer = collisions.ReferenceFrameFixer()
        
        self.full_reset() # starts game from scratch
        
    def pre_event_update(self):
        player = self.get_player()
        if player.is_crushed == True:
            player.is_alive = False
        if player.is_alive == False and not self.settings.invincible_mode():
            player.is_alive = True
            self.death_count += 1
            self.reset_level(reset_ghost=True)
        if self.get_player().finished_level:
            self.next_level(True)
    
    def handle_event(self, event):
        InGameState.handle_event(self, event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_r:
                self.death_count += 1
                self.reset_level(reset_player=True, reset_ghost=True)
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.full_reset()
                return True
            elif event.key == pygame.K_e and self.settings.dev_mode():
                self.state_manager.set_current_state(GameStateManager.EDITING_STATE)
                return True
            elif event.key == pygame.K_k and self.settings.dev_mode():
                self.settings.set_invincible_mode(not self.settings.invincible_mode())
            elif event.key == pygame.K_RIGHT and self.settings.dev_mode():
                self.next_level()
                return True
            elif event.key == pygame.K_LEFT:
                self.prev_level()
                return True
            elif event.key == pygame.K_DOWN and self.settings.dev_mode():
                self.reset_level(False, reset_ghost=False)
                return True                    
    
    def update(self, dt):
        self.add_time(dt)
        
        if self.keys['jump']:
            self.get_player().jump_action()
            self.keys['jump'] = False
        
        if bool(self.keys['left']) ^ bool(self.keys['right']):
            if self.keys['left']: 
                self.get_player().move_action(-1)
            elif self.keys['right']: 
                self.get_player().move_action(1)
        else:
            self.get_player().apply_friction(dt)
        
        self.ghost_recorder.update(dt)
        self.get_player().update(dt) 
        
        if self.settings.frozen_mode():
            dt = 0
        
        for item in self.get_entities():
            if item is not self.get_player():
                item.update(dt)
        
        self.pusher.solve_collisions(self.get_entities())
        self.rf_fixer.solve_rfs(self.get_entities())
        
        self.platformer_instance.current_level().bring_out_yer_dead()
    
    def draw(self, screen):
        self.get_drawer().update_camera(self.get_player(), screen.get_width(), screen.get_height())
        self.get_drawer().draw(screen, self.get_entities(), self.get_current_level().background_color)
        self.draw_gui(screen)
     
    def add_time(self, t):
        self.total_time += 1
        self.level_time += 1
    
    def reset_level(self, reset_player=True, reset_ghost=True):
        player = self.get_player()
        x = player.x()
        y = player.y()
        
        self.ghost_recorder.clear()
        player.reset()
        self.platformer_instance.load_level(reset_ghost)
        
        if not reset_player:
            player.set_xy(x,y)
        else:
            self.level_time = 0
    
    def full_reset(self):
        self.get_player().reset()
        self.ghost_recorder.clear()
        self.platformer_instance.set_level_num(0)
        self.total_time = 0
        self.level_time = 0
        self.death_count = 0
        self.platformer_instance.load_level()
        utilities.log("\nGame Start!")
    
    def next_level(self, update_highscore=False):
        level_num = self.get_level_num() 
        if update_highscore:  
            self.platformer_instance.level_manager.update_level_highscore(level_num, self.level_time, self.ghost_recorder)
            
        if level_num == self.get_level_manager().get_num_levels() - 1:
            self.full_reset()
        else:   
            self.platformer_instance.set_level_num(level_num + 1)
            self.level_time = 0
            self.get_player().reset()
            self.ghost_recorder.clear()
            self.platformer_instance.load_level()
      
    def prev_level(self):
        level_num = self.get_level_num()
        if not self.settings.dev_mode() and level_num == 0:
            return
        self.platformer_instance.set_level_num((level_num - 1) % self.get_level_manager().get_num_levels())
        self.platformer_instance.load_level()
        self.reset_level(reset_player=True, reset_ghost=True)
    
    def draw_gui(self, screen):
        standard_width = HardSettings.standard_size()[0]
        standard_height = HardSettings.standard_size()[1]
        xoffset = (screen.get_width() - standard_width) / 2
        yoffset = (screen.get_height() - standard_height) / 2
        
        if screen.get_width() > standard_width or screen.get_height() > standard_height:
            # so that in dev mode you can see what the actual screen size would be.
            pygame.draw.rect(screen,(255,0,0), pygame.Rect(xoffset,yoffset,standard_width,standard_height), 1)
        
        level_text = self.font.render("Level: "+str(self.get_level_num() + 1), True, (255, 255, 255))
        level_title = self.font.render(str(self.get_level_manager().current_level.name), True, (255, 255, 255))
        death_text = self.font.render("Deaths: "+str(self.death_count), True, (255, 255, 255))
        text_height = level_text.get_height()
        
        best_total_time = self.get_level_manager().get_best_run_time()
        total_time_text_color = self.get_time_display_color(self.total_time, best_total_time, start_color=(255, 255, 255), end_color=(255, 255, 255))
        total_time_text = self.font.render("Total: " + utilities.format_time(self.total_time), True, total_time_text_color)
        
        best_level_time = self.get_level_manager().get_best_level_time(self.get_level_num())
        level_time_text_color = self.get_time_display_color(self.level_time, best_level_time)
        level_time_text = self.font.render("Level: "+utilities.format_time(self.level_time), True, level_time_text_color)
        
        screen.blit(level_text, (xoffset, yoffset))
        screen.blit(level_title, (xoffset, yoffset + text_height))
        screen.blit(total_time_text, (xoffset + standard_width/2 - total_time_text.get_width()/2, yoffset))
        screen.blit(level_time_text, (xoffset + standard_width/2 - level_time_text.get_width()/2, yoffset + text_height))
        screen.blit(death_text, (xoffset + standard_width - death_text.get_width(), yoffset))
            
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

            
class EditingState(InGameState):
    SELECTED_COLOR = (255, 128, 255)
    output_dir = "saved_levels"
    def __init__(self, settings, platformer_instance):
        InGameState.__init__(self, settings, platformer_instance)
        self.selected = None
        self.selected_old_color = None
        self.build_keymapping()
        
    def pre_event_update(self):
        pass
    
    def build_keymapping(self):
        self.key_mapping = {
            pygame.K_DELETE: lambda: self.delete_selected(),
            pygame.K_e:     lambda: self.state_manager.set_current_state(GameStateManager.PLAYING_STATE),
            pygame.K_i:     lambda: self.resize_selected(0, -self._val()),
            pygame.K_j:     lambda: self.resize_selected(-self._val(), 0),
            pygame.K_k:     lambda: self.resize_selected(0, self._val()),
            pygame.K_l:     lambda: self.resize_selected(self._val(), 0),
            pygame.K_UP:    lambda: self.move_selected(0, -self._val()),
            pygame.K_DOWN:  lambda: self.move_selected(0, self._val()),
            pygame.K_LEFT:  lambda: self.move_selected(-self._val(), 0),
            pygame.K_RIGHT: lambda: self.move_selected(self._val(), 0),
            pygame.K_u:     lambda: self.duplicate_selected(),
            pygame.K_t:     lambda: self.cylcle_type_of_selected()
            
        }
        
    def _val(self):
        return 4 if self.keys["shift"] else 32
    
    def handle_event(self, event):
        InGameState.handle_event(self, event)
        
        if event.type == pygame.KEYDOWN:
            if event.key in self.key_mapping:
                self.key_mapping[event.key]()
            elif event.key == pygame.K_s and self.keys["ctrl"]:
                self.do_save()
 
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = self.get_drawer().screen_to_game_position((event.pos[0], event.pos[1]), snap_to_grid=False)
            grid_x, grid_y = self.get_drawer().screen_to_game_position((event.pos[0], event.pos[1]), snap_to_grid=True)
            utilities.log("Click at: ("+str(x)+", "+str(y)+") ["+str(grid_x)+", "+str(grid_y)+"]")
            if self.keys['ctrl']:
                pass
            elif self.keys['shift']:
                pass
            else:
                clicked_objs = self.get_level_manager().current_level.get_objects_at((x,y))
                if len(clicked_objs) > 0:
                    self.set_selected(clicked_objs[0])
                else:
                    self.set_selected(None)
            
    def update(self, dt):
        self.do_camera_move(dt)
        
        if self.settings.frozen_mode():
            dt = 0
        
        for item in self.get_entities():
            if item is not self.get_player():
                item.update(dt)
        
        self.platformer_instance.current_level().bring_out_yer_dead()
    
    def do_save(self):
    
        directory = EditingState.output_dir
        utilities.create_dir_if_doesnt_exist(directory)
        
        num = self.get_level_num()
        filename = directory + "/saved_level_" + str(num) + ".json"
        utilities.log("Saving " + filename + "...")
        curr_json = self.get_current_level().to_json()
        
        with open(filename, 'w') as outfile:
            json_string = utilities.level_json_to_string(curr_json)
            utilities.log("writing text:\n" + json_string)
            outfile.write(json_string)
        utilities.log("done.")
    
    def do_camera_move(self, dt):
        if bool(self.keys['left']) ^ bool(self.keys['right']):
            if self.keys['left']: 
                self.get_drawer().move_camera(-4, 0)
            elif self.keys['right']: 
                self.get_drawer().move_camera(4, 0)
        
        if bool(self.keys['up']) ^ bool(self.keys['down']):
            if self.keys['up']: 
                self.get_drawer().move_camera(0, -4)
            elif self.keys['down']: 
                self.get_drawer().move_camera(0, 4)
        
    def draw(self, screen):
        self.get_drawer().draw(screen, self.get_entities(), self.get_current_level().background_color)
        if self.selected != None:
            self.get_drawer().draw(screen, [self.selected], background_color=None)
        
    def switching_from(self, new_state_id):
        self.set_selected(None)
        
    def set_selected(self, obj):
        if self.selected != None:
            self.selected.set_color(self.selected_old_color)
            self.selected_old_color = None
        
        self.selected = obj
        
        if self.selected != None:
            utilities.log(str(self.selected) + " selected!")
            self.selected_old_color = self.selected.color
            self.selected.set_color(EditingState.SELECTED_COLOR)
            
    def delete_selected(self):
        if self.selected != None:
            utilities.log("deleting "+str(self.selected))
            self.get_current_level().remove_object(self.selected)
            self.set_selected(None)
            
    def resize_selected(self, width_expand, height_expand):
        if self.selected != None:
            utilities.log("stretching "+str(self.selected)+" by "+str(width_expand)+", "+str(height_expand))
            width = self.selected.width()
            height = self.selected.height()
            self.selected.set_size(max(8, width + width_expand), max(8, height + height_expand))
            
    def move_selected(self, x_move, y_move):
        if self.selected != None:
            utilities.log("moving "+str(self.selected)+" by "+str(x_move)+", "+str(y_move))
            self.selected.set_xy(self.selected.x() + x_move, self.selected.y() + y_move)
            
    def duplicate_selected(self):
        if self.selected != None:
            utilities.log("duplicating "+str(self.selected))
            if self.selected.is_block():
                selected_json = self.selected.to_json()
                new_entity = blocks.BlockFactory.from_json(selected_json)
                self.get_current_level().add_object(new_entity)
            elif self.selected.is_spawn_point():
                selected_json = self.selected.to_json()
                new_spawn = actors.SpawnPoint.from_json(selected_json)
                self.get_current_level().spawn_list.append(new_spawn) # this should be ok
            else:
                entities.log("Cannot dupe entity type: "+str(self.selected))
                
    def cylcle_type_of_selected(self):
        if self.selected != None:
            if self.selected.is_block() and not self.selected.is_moving_block(): ## can't deal with moving blocks yet
                utilities.log("Changing type of "+str(self.selected))
                types = ["normal", "bad", "finish"]
                selected_json = self.selected.to_json()
                curr_type_idx = types.index(selected_json["type"])
                if curr_type_idx == -1:
                    utilities.log("unrecognized type: "+str(selected_json["type"]))
                else:
                    selected_json["type"] = types[(curr_type_idx + 1) % len(types)]
                    new_entity = blocks.BlockFactory.from_json(selected_json)
                    
                    self.get_current_level().remove_object(self.selected)
                    self.get_current_level().add_object(new_entity)
                    self.set_selected(new_entity)
            else:
                utilities.log("Can't change type of entity: "+str(self.selected))
                
