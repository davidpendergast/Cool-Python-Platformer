#!/usr/bin/env python2.7

import pygame
pygame.init()

import blocks, actors
import drawing
import gamestate
import utilities
import options
import timer

from keybindings import KeyBindings, TAKE_SCREENSHOT
from gamestate import GameStateManager
from menustate import MainMenuState, SelectSingleLevelState
from playingstate import PlayingState, PlatformerInstance
from editingstate import EditingState

settings = options.Settings()

pygame.display.set_caption(options.title())
gamestate_manager = GameStateManager(settings)
platformer_inst = PlatformerInstance(settings)
playing = PlayingState(settings, platformer_inst)
editing = EditingState(settings, platformer_inst)
main_menu = MainMenuState(settings)
single_level = SelectSingleLevelState(settings)

gamestate_manager.set_state(GameStateManager.PLAYING_STATE, playing)
gamestate_manager.set_state(GameStateManager.EDITING_STATE, editing)
gamestate_manager.set_state(GameStateManager.MAIN_MENU_STATE, main_menu)
gamestate_manager.set_state(GameStateManager.SELECT_SINGLE_LEVEL_STATE, single_level)


gamestate_manager.set_current_state(GameStateManager.MAIN_MENU_STATE)

size = options.standard_size()
if settings.dev_mode():
    size = options.dev_size()
screen = pygame.display.set_mode(size)

still_running = True
clock = pygame.time.Clock()
FPS = options.fps()

actor = playing.get_player()  # The player's character

def stop_running(): 
    global still_running
    still_running = False

def take_screenshot():
    utilities.take_screenshot(screen)

GLOBAL_COMMANDS = {
    TAKE_SCREENSHOT: lambda: take_screenshot()
}

#ticks = 0
#display_freq = 60
#ideal_total = display_freq*1000/options.fps()
#only_print_if_slow = True

while still_running and gamestate_manager.still_running():
    gamestate_manager.pre_event_update()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            stop_running()
        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            name = pygame.key.name(event.key)
            actions = settings.get_actions_for_key(name)
            used_key = False
            for action in actions:
                if action in GLOBAL_COMMANDS and event.type == pygame.KEYDOWN:
                    GLOBAL_COMMANDS[action]()
                    used_key == True
            if not used_key:
                gamestate_manager.handle_event(event)
        else:
            gamestate_manager.handle_event(event)
    dt = 1
    gamestate_manager.update(dt)
    gamestate_manager.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)
    
    #ticks += 1
    #if ticks % display_freq == 0 and timer.has_events():
    #    if not only_print_if_slow or timer.total_time() >= ideal_total:
    #        print "\nTimings for "+str(display_freq) + " ticks: ideal_total=" + str(ideal_total)
    #        print timer.get_text_summary()
    #    timer.clear()
        
pygame.quit()
