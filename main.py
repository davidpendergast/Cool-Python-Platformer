#!/usr/bin/env python2.7

import pygame

import blocks, actors
import drawing
import gamestate
import utilities
from options import Settings
from options import HardSettings
from gamestate import GameStateManager, PlayingState, EditingState, PlatformerInstance

pygame.init()
settings = Settings()

pygame.display.set_caption("Extreme Block Jumper 2 - "+settings.level_path())
gamestate_manager = GameStateManager(settings)
platformer_inst = PlatformerInstance(settings)
playing = PlayingState(settings, platformer_inst)
editing = EditingState(settings, platformer_inst)
gamestate_manager.set_state(GameStateManager.PLAYING_STATE, playing)
gamestate_manager.set_state(GameStateManager.EDITING_STATE, editing)

gamestate_manager.set_current_state(GameStateManager.PLAYING_STATE)

size = HardSettings.standard_size()
if settings.dev_mode():
    size = HardSettings.dev_size()
screen = pygame.display.set_mode(size)

still_running = True
clock = pygame.time.Clock()
FPS = HardSettings.fps()

actor = playing.get_player()  # The player's character

def stop_running(): 
    global still_running
    still_running = False
def take_screenshot():
    utilities.take_screenshot(screen)

GLOBAL_COMMANDS = {
    pygame.K_ESCAPE: stop_running,
    pygame.K_F5: take_screenshot
}

while still_running:
    gamestate_manager.pre_event_update()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            stop_running()
        elif event.type == pygame.KEYDOWN and event.key in GLOBAL_COMMANDS:
            GLOBAL_COMMANDS[event.key]()
        else:
            gamestate_manager.handle_event(event)
            
    dt = 1
    gamestate_manager.update(dt)
    gamestate_manager.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
