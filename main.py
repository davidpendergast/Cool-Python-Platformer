#!/usr/bin/env python

import pygame

import phys_objects
import drawing
import gamestate

import server
import client

pygame.init()

game = gamestate.PlayingState()

size = (640, 480)
if game.DEV_MODE:
    size = (size[0]+200, size[1]+200)
screen = pygame.display.set_mode(size)

still_running = True
clock = pygame.time.Clock()
FPS = 60

current_gamestate = game
actor = game.player  # The player's character

client.connect(actor, game)

while still_running:
    current_gamestate.pre_event_update()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            still_running = False
        else:
            current_gamestate.handle_event(event)
            
    dt = 100/FPS
    game.update(dt)
    game.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

client.disconnect()

pygame.quit()
