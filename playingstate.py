from keybindings import *

import pygame
import sys
import json
import os
import random

from gamestate import GameState, GameStateManager

import blocks, actors
import drawing
import levels
import collisions
import options
import utilities
import timer

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

        self.font = options.get_font(30)
    
    def configure_keybindings(self):
        GameState.configure_keybindings(self)
        
        self.keydown_action_map.update({
            QUIT:           lambda: self.state_manager.set_current_state(GameStateManager.MAIN_MENU_STATE),
            PAUSE:          lambda: None,
            SHOW_GRID:      lambda: self.settings.set_show_grid(not self.settings.show_grid()),
            TOGGLE_3D:      lambda: self.settings.set_draw_3d(not self.settings.draw_3d()),
            FREEZE_MODE:    lambda: self.settings.set_frozen_mode(not self.settings.frozen_mode()) if self.settings.edit_mode() else None
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
        if prev_state_id != GameStateManager.EDITING_STATE and prev_state_id != GameStateManager.PLAYING_STATE:
            if self.settings.edit_mode():
                options.set_resizable(True, size=options.dev_size())
            else:
                options.set_resizable(False, size=options.standard_size())


class PlayingState(InGameState):
    def __init__(self, settings, platformer_instance):
        InGameState.__init__(self, settings, platformer_instance)
        
        self.ghost_recorder = actors.GhostRecorder(self.get_player())
        self.death_count = 0
        
        self.total_time = 0
        self.level_time = 0
        
        self.death_countdown = 0
        
        self.pusher = collisions.CollisionFixer()
        self.rf_fixer = collisions.ReferenceFrameFixer()
        
        self.full_reset() # starts game from scratch
        
    def switching_to(self, prev_state_id):
        InGameState.switching_to(self, prev_state_id)
        if prev_state_id != GameStateManager.EDITING_STATE:
            self.full_reset()
        
    def configure_keybindings(self):
        InGameState.configure_keybindings(self)
            
        self.keydown_action_map.update({
            JUMP:               lambda: self.set_keystate("jump", True),
            MOVE_LEFT:          lambda: self.set_keystate("left", True),
            MOVE_RIGHT:         lambda: self.set_keystate("right", True),
            QUIT:               lambda: self.state_manager.set_current_state(GameStateManager.MAIN_MENU_STATE),
            PAUSE:              lambda: None,
            RESET_LEVEL:        lambda: self.get_player().kill("spontaneous combustion."),#self.reset_level(reset_player=True, death_increment=1, reset_ghost=True),
            RESET_RUN:          lambda: self.full_reset(),
            PREVIOUS_LEVEL:     lambda: self.prev_level(),
            RESET_LEVEL_SOFT:   lambda: self.reset_level(False, reset_ghost=False) if self.settings.edit_mode() else None,
            TOGGLE_EDIT_MODE:   lambda: self.state_manager.set_current_state(GameStateManager.EDITING_STATE) if self.settings.edit_mode() else None,
            INVINCIBLE_MODE:    lambda: self.settings.set_invincible_mode(not self.settings.invincible_mode()) if self.settings.edit_mode() else None,
            NEXT_LEVEL:         lambda: self.next_level() if self.settings.edit_mode() else None
        })
        
        self.keyup_action_map.update({
            MOVE_LEFT:  lambda: self.set_keystate("left", False),
            MOVE_RIGHT: lambda: self.set_keystate("right", False)
        })
        
    def pre_event_update(self):
        player = self.get_player()
        if player.is_crushed:
            player.is_alive = False
        if not player.is_alive and not self.settings.invincible_mode() and self.death_countdown == 0:
            self.initiate_death_sequence()  
        elif self.get_player().finished_level:
            self.next_level(True)
            
        if self.death_countdown == 1:
            self.finalize_death_sequence()
    
    def initiate_death_sequence(self):
        self.death_count += 1
        self.death_countdown = 100
        self.add_blood(self.get_player(), 100)
    
    def finalize_death_sequence(self):
        self.get_player().is_alive = True
        self.reset_level(reset_ghost=True)
        
    def handle_event(self, event):
        done = InGameState.handle_event(self, event)
        return done                
    
    def update(self, dt):
        self.add_time(dt)
        timer.start("updating player", "update")
        if self.keystate['jump'] or self.get_player().jump_buffer > 0:
            self.get_player().jump_action()
            self.keystate['jump'] = False
        
        if bool(self.keystate['left']) ^ bool(self.keystate['right']):
            if self.keystate['left']: 
                self.get_player().move_action(-1)
            elif self.keystate['right']: 
                self.get_player().move_action(1)
        else:
            self.get_player().apply_friction(dt)
        
        if self.death_countdown == 0:
            self.ghost_recorder.update(dt)
            self.get_player().update(dt) 
        
        if self.settings.frozen_mode():
            dt = 0
        timer.end("updating player")
        
        timer.start("updating everything", "update")
        for item in self.get_entities():
            if item is not self.get_player():
                item.update(dt)
        timer.end("updating everything")
        
        timer.start("collisions", "update")
        self.pusher.solve_collisions(self.get_entities())
        self.rf_fixer.solve_rfs(self.get_entities())
        timer.end("collisions")
        
        dead = self.platformer_instance.current_level().bring_out_yer_dead()
        for x in dead:
            if x.is_actor() and x is not self.get_player():
                self.add_blood(x)
    
    def draw(self, screen):
        w = screen.get_width()
        h = screen.get_height()
        self.get_drawer().update_camera(self.get_player(), w, h)
        self.get_drawer().draw_level(screen, self.get_current_level())
        self.draw_gui(screen)
     
    def add_time(self, t):
        self.total_time += 1
        self.level_time += 1
        if self.death_countdown > 1:
            self.death_countdown -= 1
        
    def add_blood(self, entity, lifespan=100):
        color = entity.color
        num = 10
        for _ in xrange(0, num):
            v = ((0.5 - random.random())*10, (0.5 - random.random())*10)
            blood = actors.Particle(entity.x(), entity.y(), 10, v, color, lifespan)
            self.get_current_level().add_object(blood)
    
    def reset_level(self, reset_player=True, death_increment=0, reset_ghost=True):
        self.death_count += death_increment
        self.death_countdown = 0
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
        self.death_countdown = 0
        
        if self.settings.single_level_mode():
            start_level = self.settings.single_level_num()
        else:
            start_level = 0
            
        self.platformer_instance.set_level_num(start_level)
        self.total_time = 0
        self.level_time = 0
        self.death_count = 0
        self.platformer_instance.load_level()
        utilities.log("Game Start!")
    
    def next_level(self, update_highscore=False):
        level_num = self.get_level_num() 
        if update_highscore:  
            self.platformer_instance.level_manager.update_level_highscore(level_num, self.level_time, self.ghost_recorder)
        
        is_last_level = level_num == self.get_level_manager().get_num_levels() - 1
        
        if self.settings.single_level_mode() or is_last_level:
            self.full_reset()
        else:   
            self.platformer_instance.set_level_num(level_num + 1)
            self.level_time = 0
            self.get_player().reset()
            self.ghost_recorder.clear()
            self.platformer_instance.load_level()
      
    def prev_level(self):
        if self.settings.single_level_mode():
            return
            
        level_num = self.get_level_num()
        if not self.settings.edit_mode() and level_num == 0:
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
        if self.settings.single_level_mode():
            screen.blit(level_time_text, (xoffset + standard_width/2 - level_time_text.get_width()/2, yoffset))
        else:
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
