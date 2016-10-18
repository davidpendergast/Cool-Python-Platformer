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
        self.keystate = {
            "shift":False,
            "ctrl":False
        }
        
        self.configure_keybindings()
    def pre_event_update(self):
        pass
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:    
            keyname = pygame.key.name(event.key)
            actions = self.settings.get_actions_for_key(keyname)
            
            if len(actions) > 0:
                if event.type == pygame.KEYDOWN:
                    action_map = self.keydown_action_map
                else:
                    action_map = self.keyup_action_map
                    
                for action in actions:
                    if action in action_map:
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
