from keybindings import *

import pygame
import sys
import json
import os

import blocks, actors
import drawing
import levels
import collisions
import options
import utilities

class GameState:
    def __init__(self, settings):
        self.state_manager = None # gets set when gamestate is added to a manager
        self.font = pygame.font.Font(pygame.font.match_font("consolas", bold=True), 24)
        self.settings = settings
        
        self.keydown_action_map = {}
        self.keyup_action_map = {}
        self.key_bindings = KeyBindings([], self.settings)
        self.keystate = {
            "shift":False,
            "ctrl":False
        }
        
        self.configure_keybindings()
    def pre_event_update(self):
        pass
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            
            name = pygame.key.name(event.key)
            if self.key_bindings.has_binding(name):
                action = self.key_bindings.get_action(name)
                action_map = self.keydown_action_map if event.type == pygame.KEYDOWN else self.keyup_action_map
                if action in action_map:
                    # print "pressed: "+str(name)+", performing action: "+str(action)
                    action_map[action]() 
                    return True
        return False
                    
    def update(self, dt):
        pass
    def draw(self, screen):
        pass
    def switching_to(self, prev_state_id):
        pass
    def switching_from(self, new_state_id):
        pass
    def configure_keybindings(self):
        self.key_bindings.add_actions([SHIFT, CTRL])
        self.keydown_action_map.update({
            SHIFT: lambda: self.set_keystate("shift", True),
            CTRL: lambda: self.set_keystate("ctrl", True),
        })
        self.keyup_action_map.update({
            SHIFT: lambda: self.set_keystate("shift", False),
            CTRL: lambda: self.set_keystate("ctrl", False),
        })
    def set_keystate(self, key, value):
        self.keystate[key] = value
        
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
        self.full_quit = False
        
    def still_running(self):
        return not self.full_quit
    
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
            
class MainMenuState(GameState):
    def __init__(self, settings):
        GameState.__init__(self, settings)
        self.title_font = pygame.font.Font(pygame.font.match_font("consolas", bold=True), 60)
        self.icing = 30
        self.selected_color = (255,255,0)
        self.unselected_color = (255,255,255)
        self.background_color = (0,0,0)
        self.title_image = self.get_title_text_image(options.title(), options.standard_size()[0] - 2*self.icing)
        self.option_names = ["start full run", "grind single level", "edit levels", "select level pack", "settings"]
        self.selected_index = 0
        self.option_text_images = []
        for i in range(0, len(self.option_names)):
            name = self.option_names[i]
            c = self.unselected_color if i != self.selected_index else self.selected_color
            self.option_text_images.append(self.font.render(name, True, c))
        
    def configure_keybindings(self):
        actions = [MENU_UP, MENU_DOWN, MENU_CONFIRM, QUIT]
        self.key_bindings.add_actions(actions)
        self.keydown_action_map.update({
            MENU_UP: lambda: self.set_selected_index(self.selected_index-1),
            MENU_DOWN: lambda: self.set_selected_index(self.selected_index+1),
            MENU_CONFIRM: lambda: self.state_manager.set_current_state(GameStateManager.PLAYING_STATE),
            QUIT: lambda: self._full_exit()
        })
        
    def _full_exit(self):
        self.state_manager.full_quit = True
        
    def handle_event(self, event):
        GameState.handle_event(self, event)
    
    def set_selected_index(self, new_index):
        new_index = new_index % len(self.option_names)
        self.option_text_images[self.selected_index] = self.font.render(self.option_names[self.selected_index], True, self.unselected_color)
        self.option_text_images[new_index] = self.font.render(self.option_names[new_index], True, self.selected_color)
        self.selected_index = new_index
        
    def update(self, dt):
        pass
        
    def draw(self, screen):
        screen.fill(self.background_color)
        standard_width = options.standard_size()[0]
        standard_height = options.standard_size()[1]
        xoffset = (screen.get_width() - standard_width) / 2
        yoffset = (screen.get_height() - standard_height) / 2
        
        if screen.get_width() > standard_width or screen.get_height() > standard_height:
            # so that in dev mode you can see what the actual screen size would be.
            pygame.draw.rect(screen,(255,0,0), pygame.Rect(xoffset,yoffset,standard_width,standard_height), 1)
        
        screen.blit(self.title_image, (xoffset + self.icing, yoffset + self.icing))
        option_heights = [x.get_height() for x in self.option_text_images]
        options_height = sum(option_heights)
        options_width = max([x.get_width() for x in self.option_text_images])
        for i in range(0, len(self.option_text_images)):
            opt = self.option_text_images[i]
            xpos = xoffset + standard_width - options_width - self.icing
            ypos = yoffset + standard_height - options_height + sum(option_heights[0:i]) - self.icing
            screen.blit(opt, (xpos, ypos))
            
        level_pack = self.settings.level_path()
        level_pack_image = self.font.render(level_pack, True, self.unselected_color)
        screen.blit(level_pack_image, (xoffset + self.icing, yoffset + self.title_image.get_height() + self.icing))
                
    def get_title_text_image(self, title_str, max_width):
        lines = []
        words = title_str.split(" ")
        start_line = 0
        end_line = 0
        while end_line < len(words):
            text = " ".join(words[start_line:end_line+1])
            image = self.title_font.render(text, True, self.unselected_color)
            if image.get_width() > max_width:
                if start_line == end_line:
                    # word itself is too long, just cram it in there
                    lines.append(image)
                    start_line = end_line + 1
                    end_line = end_line + 1
                else:
                    # line is one word too wide
                    text = " ".join(words[start_line:end_line])
                    image = self.title_font.render(text, True, self.unselected_color)
                    lines.append(image)
                    start_line = end_line
            else:
                end_line += 1
        if start_line < end_line:
            text = " ".join(words[start_line:end_line])
            image = self.title_font.render(text, True, self.unselected_color)
            lines.append(image)
            
        total_height = sum([x.get_height() for x in lines])
        total_width = max([x.get_width() for x in lines])
        result = pygame.Surface((total_width, total_height))
        
        y = 0
        for line in lines:
            result.blit(line, (0, y))
            y += line.get_height()
        
        return result


class PlatformerInstance:
    "state that's shared between PlayingState and EditingState"
    def __init__(self, settings):
        self.settings = settings
        self.player = actors.Actor(24, 32, settings.get_color())
        self.player.is_player = True
        self.level_manager = levels.LevelManager(self.settings)
        self.drawer = drawing.Drawer(settings)
        
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

        self.keystate.update({
            'left':False, 
            'right':False, 
            'jump':False,
            'up':False,
            'down':False,
        })

        self.mouse_down_pos = None
        self.font = pygame.font.Font(pygame.font.match_font("consolas", bold=True), 24)
    
    def configure_keybindings(self):
        GameState.configure_keybindings(self)
        actions = [QUIT, PAUSE, PREVIOUS_LEVEL, SHOW_GRID]
        if self.settings.dev_mode():
            actions = actions + [NEXT_LEVEL, FREEZE_MODE]
        self.key_bindings.add_actions(actions)
        
        self.keydown_action_map.update({
            QUIT:           lambda: self.state_manager.set_current_state(GameStateManager.MAIN_MENU_STATE),
            PAUSE:          lambda: None,
            SHOW_GRID:      lambda: self.settings.set_show_grid(not self.settings.show_grid()),
            FREEZE_MODE:    lambda: self.settings.set_frozen_mode(not self.settings.frozen_mode()),
            NEXT_LEVEL:     lambda: self.next_level(),
            PREVIOUS_LEVEL: lambda: self.prev_level()
        })
    
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
        return GameState.handle_event(self, event)
    
    def switching_to(self, prev_state_id):
        for key in self.keystate:
            self.keystate[key] = False


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
        
    def configure_keybindings(self):
        InGameState.configure_keybindings(self)
        actions = [] + PLAYER_MOVES + [RESET_RUN, RESET_LEVEL]
        if self.settings.dev_mode():
            actions = actions + [INVINCIBLE_MODE, RESET_LEVEL_SOFT, TOGGLE_EDIT_MODE]
            
        self.key_bindings.add_actions(actions)
        self.keydown_action_map.update({
            JUMP :              lambda: self.set_keystate("jump", True),
            MOVE_LEFT :         lambda: self.set_keystate("left", True),
            MOVE_RIGHT :        lambda: self.set_keystate("right", True),
            QUIT:               lambda: self.state_manager.set_current_state(GameStateManager.MAIN_MENU_STATE),
            PAUSE:              lambda: None,
            RESET_LEVEL:        lambda: self.reset_level(reset_player=True, death_increment=1, reset_ghost=True),
            RESET_LEVEL_SOFT:   lambda: self.reset_level(False, reset_ghost=False),
            RESET_RUN:          lambda: self.full_reset(),
            TOGGLE_EDIT_MODE:   lambda: self.state_manager.set_current_state(GameStateManager.EDITING_STATE),
            INVINCIBLE_MODE:    lambda: self.settings.set_invincible_mode(not self.settings.invincible_mode()),
            NEXT_LEVEL:         lambda: self.next_level(),
            PREVIOUS_LEVEL:     lambda: self.prev_level(),
            RESET_LEVEL:        lambda: self.reset_level(reset_player=True, death_increment=1, reset_ghost=True),
            RESET_LEVEL_SOFT:   lambda: self.reset_level(False, reset_ghost=False),
        })
        self.keyup_action_map.update({
            MOVE_LEFT:  lambda: self.set_keystate("left", False),
            MOVE_RIGHT: lambda: self.set_keystate("right", False)
        })
        
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
        done = InGameState.handle_event(self, event)
        return done                
    
    def update(self, dt):
        self.add_time(dt)
        
        if self.keystate['jump']:
            self.get_player().jump_action()
            self.keystate['jump'] = False
        
        if bool(self.keystate['left']) ^ bool(self.keystate['right']):
            if self.keystate['left']: 
                self.get_player().move_action(-1)
            elif self.keystate['right']: 
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
    
    def reset_level(self, reset_player=True, death_increment=0, reset_ghost=True):
        self.death_count += death_increment
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
        standard_width = options.standard_size()[0]
        standard_height = options.standard_size()[1]
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
        
    def pre_event_update(self):
        pass
        
    def configure_keybindings(self):
        InGameState.configure_keybindings(self)
        actions = CAMERA_DIRS + RESIZE_DIRS + TRANSLATE_DIRS
        actions += [DUPLICATE_SELECTED, CYCLE_SELECTED_TYPE, TOGGLE_EDIT_MODE, SAVE_LEVEL, DELETE_SELECTED]
        self.key_bindings.add_actions(actions)
        
        self.keydown_action_map.update({
            CAMERA_UP:              lambda: self.set_keystate("up", True), 
            CAMERA_LEFT:            lambda: self.set_keystate("left", True), 
            CAMERA_RIGHT:           lambda: self.set_keystate("right", True), 
            CAMERA_DOWN:            lambda: self.set_keystate("down", True), 
            RESIZE_LEFT:            lambda: self.resize_selected(-self._val(), 0),
            RESIZE_UP:              lambda: self.resize_selected(0, -self._val()),
            RESIZE_RIGHT:           lambda: self.resize_selected(self._val(), 0),
            RESIZE_DOWN:            lambda: self.resize_selected(0, self._val()),
            TRANSLATE_LEFT:         lambda: self.move_selected(-self._val(), 0),
            TRANSLATE_UP:           lambda: self.move_selected(0, -self._val()),
            TRANSLATE_RIGHT:        lambda: self.move_selected(self._val(), 0),
            TRANSLATE_DOWN:         lambda: self.move_selected(0, self._val()),
            TOGGLE_EDIT_MODE:       lambda: self.state_manager.set_current_state(GameStateManager.PLAYING_STATE),
            SAVE_LEVEL:             lambda: self.do_save(),
            DUPLICATE_SELECTED:     lambda: self.duplicate_selected(),
            CYCLE_SELECTED_TYPE:    lambda: self.cylcle_type_of_selected(),
            DELETE_SELECTED:        lambda: self.delete_selected()
        })
        self.keyup_action_map.update({
            CAMERA_UP:      lambda: self.set_keystate("up", False), 
            CAMERA_LEFT:    lambda: self.set_keystate("left", False), 
            CAMERA_RIGHT:   lambda: self.set_keystate("right", False), 
            CAMERA_DOWN:    lambda: self.set_keystate("down", False), 
        })
        
    def _val(self):
        return 4 if self.keystate["shift"] else 32
    
    def handle_event(self, event):
        InGameState.handle_event(self, event)
 
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = self.get_drawer().screen_to_game_position((event.pos[0], event.pos[1]), snap_to_grid=False)
            grid_x, grid_y = self.get_drawer().screen_to_game_position((event.pos[0], event.pos[1]), snap_to_grid=True)
            utilities.log("Click at: ("+str(x)+", "+str(y)+") ["+str(grid_x)+", "+str(grid_y)+"]")
            if self.keystate['ctrl']:
                pass
            elif self.keystate['shift']:
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
        if bool(self.keystate['left']) ^ bool(self.keystate['right']):
            if self.keystate['left']: 
                self.get_drawer().move_camera(-4, 0)
            elif self.keystate['right']: 
                self.get_drawer().move_camera(4, 0)
        
        if bool(self.keystate['up']) ^ bool(self.keystate['down']):
            if self.keystate['up']: 
                self.get_drawer().move_camera(0, -4)
            elif self.keystate['down']: 
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
                
