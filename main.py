#!/usr/bin/env python

import pygame,phys_objects,drawing,gamestate
import server
import client

pygame.init()

size = (320*2,240*2)
screen = pygame.display.set_mode(size)

still_running = True
clock = pygame.time.Clock()
FPS = 60

camera = (0,0)

pusher = phys_objects.CollisionFixer()
rf_fixer = phys_objects.ReferenceFrameFixer()
drawer = drawing.Drawer()
game = gamestate.Game()
actor = game.actor
group = game.group 

DEV_MODE = True

mouse_down_pos = None

invincible_mode = False

keys = {'left':False,'right':False,'jump':False}

client.connect(actor, game)

while still_running:
	if actor.is_crushed == True:
		actor.is_alive = False
	if actor.is_alive == False and not invincible_mode:	#move this stuff to gamestate.py
		actor.is_alive = True
		game.death_count += 1
		game.reset_level()
	if actor.finished_level:
		game.next_level(True)
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			still_running = False
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a:
				keys['left']=True
			elif event.key == pygame.K_d:
				keys['right']=True
			elif event.key == pygame.K_w:
				keys['jump']=True
			elif event.key == pygame.K_RETURN or event.key == pygame.K_r:
				game.death_count += 1
				game.reset_level()
			elif event.key == pygame.K_g:
				drawer.show_grid = not drawer.show_grid
			elif event.key == pygame.K_k and DEV_MODE:
				invincible_mode = not invincible_mode
			elif event.key == pygame.K_RIGHT and DEV_MODE:
				game.next_level()
				continue
			elif event.key == pygame.K_LEFT and DEV_MODE:
				game.prev_level()
				continue
			elif event.key == pygame.K_ESCAPE:
				still_running = False
				break
		elif event.type == pygame.KEYUP:
			if event.key == pygame.K_a:
				keys['left']=False
			elif event.key == pygame.K_d:
				keys['right']=False
			elif event.key == pygame.K_w:
				keys['jump']=False
		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			x = event.pos[0]+drawer.camera_pos[0]
			y = event.pos[1]+drawer.camera_pos[1]
			mouse_down_pos = (x,y)
			print "Mouse Click at: ("+str(x)+", "+str(y)+") ["+str(x - (x % drawer.grid_spacing))+", "+str(y - (y % drawer.grid_spacing))+"]"
		elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
			x = event.pos[0]+drawer.camera_pos[0]
			y = event.pos[1]+drawer.camera_pos[1]
			grid_x = x - (x % drawer.grid_spacing)
			grid_y = y - (y % drawer.grid_spacing)
			if mouse_down_pos != None:
				grid_down_x = mouse_down_pos[0] - (mouse_down_pos[0] % drawer.grid_spacing)
				grid_down_y = mouse_down_pos[1] - (mouse_down_pos[1] % drawer.grid_spacing)
				if grid_x != grid_down_x or grid_y != grid_down_y:
					#mouse has been dragged across more than one grid square.
					print "Mouse Dragged to form rectangle:["+str(grid_down_x)+", "+str(grid_down_y)+", "+str(grid_x - grid_down_x)+", "+str(grid_y - grid_down_y)+"]"
					
	
	if bool(keys['left']) ^ bool(keys['right']):
		if keys['left']: 
			actor.move_action(-1)
		elif keys['right']: 
			actor.move_action(1)
	else:
		#Friction
		fric = 0.1
		if actor.is_grounded:
			fric = 1
		#Move this stuff to Actor...
		vx = actor.vx()
		if vx < fric and vx > -fric:
			vx = 0
		else:
			if vx < 0:
				vx = vx + fric
			else:
				vx = vx - fric
		actor.set_vx(vx)
	if keys['jump']:
		actor.jump_action()
		keys['jump'] = False
	
	dt = 100/FPS
	game.add_time()
	group.update(dt)
	pusher.solve_collisions(group)
	rf_fixer.solve_rfs(group)

	drawer.update_camera(actor, size[0], size[1])
	drawer.draw(screen, client.get_ghosts())
	drawer.draw(screen, group)

	game.draw_gui(screen)
	pygame.display.flip()
	clock.tick(FPS)

client.disconnect()

pygame.quit()
