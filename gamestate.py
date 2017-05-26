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
        self.font = options.get_font(30)
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
        "called when state is activated"
        pass
    def switching_from(self, new_state_id):
        "called when state is deactivated"
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
    SELECT_SINGLE_LEVEL_STATE = "select_single_level_state"
    
    def __init__(self, settings):
        self.states = {
            GameStateManager.MAIN_MENU_STATE:None,
            GameStateManager.PLAYING_STATE:None,
            GameStateManager.EDITING_STATE:None,
            GameStateManager.GAME_OVER_STATE:None,
            GameStateManager.SELECT_SINGLE_LEVEL_STATE:None
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
