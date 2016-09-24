#!/usr/bin/env python2.7

import pygame

import phys_objects
import drawing
import gamestate
from options import Settings
from options import HardSettings

pygame.init()

settings = Settings()
game = gamestate.PlayingState(settings)

size = HardSettings.standard_size()
if settings.dev_mode():
    size = HardSettings.dev_size()
screen = pygame.display.set_mode(size)

still_running = True
clock = pygame.time.Clock()
FPS = HardSettings.fps()

current_gamestate = game
actor = game.player  # The player's character

while still_running:
    current_gamestate.pre_event_update()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            still_running = False
        else:
            current_gamestate.handle_event(event)
            
    dt = 1
    game.update(dt)
    game.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
