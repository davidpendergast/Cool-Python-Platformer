#!/usr/bin/env python2.7

import pygame

import blocks, actors
import drawing
import gamestate
import utilities
import options

from keybindings import KeyBindings, TAKE_SCREENSHOT
from gamestate import GameStateManager, PlayingState, EditingState, MainMenuState, PlatformerInstance

pygame.init()
settings = options.Settings()

pygame.display.set_caption("Extreme Block Jumper 2 - "+settings.level_path())
gamestate_manager = GameStateManager(settings)
platformer_inst = PlatformerInstance(settings)
playing = PlayingState(settings, platformer_inst)
editing = EditingState(settings, platformer_inst)
main_menu = MainMenuState(settings)
gamestate_manager.set_state(GameStateManager.PLAYING_STATE, playing)
gamestate_manager.set_state(GameStateManager.EDITING_STATE, editing)
gamestate_manager.set_state(GameStateManager.MAIN_MENU_STATE, main_menu)

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

GLOBAL_BINDINGS = KeyBindings([TAKE_SCREENSHOT], settings)
GLOBAL_COMMANDS = {
    TAKE_SCREENSHOT: lambda: take_screenshot()
}

while still_running and gamestate_manager.still_running():
    gamestate_manager.pre_event_update()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            stop_running()
        elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            name = pygame.key.name(event.key)
            if GLOBAL_BINDINGS.has_binding(name) and event.type == pygame.KEYDOWN:
                GLOBAL_COMMANDS[GLOBAL_BINDINGS.get_action(name)]()
            else:
                gamestate_manager.handle_event(event)
        else:
            gamestate_manager.handle_event(event)
    dt = 1
    gamestate_manager.update(dt)
    gamestate_manager.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
