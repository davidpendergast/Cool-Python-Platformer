import pygame, sets, math, random

class Box(pygame.sprite.Sprite):
	def __init__(self,width,height,color=(128,128,128), border_color=None):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((width,height))
		
		self.color = color
		self.border_color = border_color
		self.repaint()
	
		self.is_solid = True		#Whether this box prevents movement of other solid boxes
		self.is_pushable = True		#Whether the collision fixer can move this object
		self.is_visible = True		#Whether this box renders.
		self.has_physics = True
		
		#self.color = color
		#self.border_color = border_color
		
		self.rect = pygame.Rect(0,0,width,height)
		self.v = (0,0)
		self.a = (0,0.3)
		
		self.max_vy = 10
		self.max_vx = 5
		
		self.rf_parent = None			#physics reference frame information. For example, when an actor stands on a moving platform
		self.rf_children = sets.Set()	#or is stuck to another object, it will enter that object's reference frame.
		
	#dt = time delta of the current tick, in ms.
	def update(self,dt):
		if self.has_physics:
			self.apply_physics(dt)
		
	def apply_physics(self, dt):
		vx = self.v[0] + self.a[0]*dt
		if vx > self.max_vx:
			vx = self.max_vx
		elif vx < -self.max_vx:
			vx = -self.max_vx
		self.v = (vx, self.v[1] + self.a[1]*dt) 
		if abs(vx) < 1:
			vx = 0
		self.move(vx*dt, self.v[1]*dt, True)
	def move(self, dx, dy, move_at_least_1=False):
		"Moves this object and all children in reference frame"
		if move_at_least_1 and dx != 0 and abs(dx) < 1:
			dx = math.copysign(1,dx)
		if move_at_least_1 and dy != 0 and abs(dy) < 1:
			dy = math.copysign(1,dy)	
		self.rect.move_ip(dx,dy)
		for kid in self.rf_children:
			kid.rect.move_ip(dx,dy)
	def set_x(self, x):
		dx = x - self.x()
		self.move(dx, 0)
		return self
	def set_y(self, y):
		dy = y - self.y()
		self.move(0, dy)
		return self
	def set_xy(self, x, y):
		self.set_x(x)
		self.set_y(y)
		return self
	def x(self):
		return self.rect.x
	def y(self):
		return self.rect.y
	def set_vx(self, vx):
		if vx > self.max_vx:
			vx = self.max_vx
		elif vx < -self.max_vx:
			vx = -self.max_vx
		self.v = (vx, self.v[1])
	def set_vy(self, vy):
		if vy > self.max_vy:
			vy = self.max_vy
		elif vy < -self.max_vy:
			vy = -self.max_vy
		self.v = (self.v[0], vy)
	def vx(self):
		return self.v[0]
	def vy(self):
		return self.v[1]
	def set_ax(self, ax):
		self.a = (ax, self.a[1])
	def add_to_rf(self, other):
		other.rf_parent = self
		self.rf_children.add(other)
	def remove_from_rf(self, other):
		assert other.rf_parent == self and other in self.rf_children, "Error: Attempting disjointed rf removal"
		other.rf_parent = None
		self.rf_children.remove(other)
	def is_still_rf_child_of(self, parent):
		assert self.rf_parent == parent, "Error: Disjointed rf parent-child check"
		bool = self.rect.left < parent.rect.right and self.rect.right > parent.rect.left	#horizontally aligned
		bool = bool and abs(self.rect.bottom - parent.rect.top) < 0.5						#directly on top of parent
		return bool
	def collided_with(self, obj, direction="NONE"):
		"direction = side of self that touched obj. Valid inputs are TOP, BOTTOM, LEFT, RIGHT, NONE"
		pass
	def set_color(self, color):
		self.color = color
		self.repaint()
	def set_border_color(self, color):
		self.border_color = color
		self.repaint()
	def repaint(self):
		if self.border_color == None:
			self.border_color = self.color
		self.image.fill(self.border_color)
		b_thickness = 2
		self.image.fill(self.color, (b_thickness,b_thickness,self.image.get_width()-b_thickness*2,self.image.get_height()-b_thickness*2))
	
class Block(Box):
	BAD_COLOR = (255,0,0)
	NORMAL_COLOR = (128,128,128)
	def __init__(self, width, height, color=None, border_color=None): 
		color = self.perturb_color(Block.NORMAL_COLOR, 20) if color == None else color
		Box.__init__(self, width, height, color, border_color)
		self.is_solid = True
		self.is_pushable = False
		self.is_visible = True
		self.a = (0,0)
	
	def update(self, dt):
		pass
		
	def perturb_color(self,orig_color, max_perturb, only_greyscale=True):
		if only_greyscale:
			pert = random.randint(0,20)
			if random.random() > 0.5:
				pert = -pert
			return (orig_color[0]+pert, orig_color[1]+pert, orig_color[2]+pert)
		else:
			return orig_color

class MovingBlock(Block):
	def __init__(self, width, height, x_fun, y_fun, color=None, border_color=None):
		Block.__init__(self,width,height, color, border_color)
		self.current_dist = 0
		self.dist_before_reverse = 32*5
		self.current_dir = 1;
		self.speed = 1;
		self.path = CustomPath(x_fun, y_fun)
		
		#vars used for switch behavior
		self.is_paused = False	
		self.pause_after_next_update = False
	def update(self, dt):
		if self.path != None and not self.is_paused:
			xy = self.path.step(dt)
			self.set_x(xy[0])
			self.set_y(xy[1])
		if self.pause_after_next_update:
			self.is_paused = True
		# else:
			# x = self.rect.x
			# if(self.current_dist > self.dist_before_reverse):
				# self.current_dir = -self.current_dir
				# self.current_dist = 0
			# self.set_vx(self.speed * self.current_dir)
			# self.set_vy(self.speed * self.current_dir)
			# self.apply_physics(dt)
			# x2 = self.rect.x
			# self.current_dist += abs(x2 - x)
	@staticmethod
	def get_up_down_block(width, height, x, y_low, y_high, t="@t*0.01*math.pi"):
		return MovingBlock(width, height, str(x), "("+str(y_low)+"+"+str(y_high)+")/2 + ("+str(y_high)+"-"+str(y_low)+")/2*math.cos("+t+")")
	@staticmethod
	def get_left_right_block(width, height, x_low, x_high, y, t="@t*0.01*math.pi"):
		return MovingBlock(width, height, "("+str(x_low)+"+"+str(x_high)+")/2 + ("+str(x_high)+"-"+str(x_low)+")/2*math.cos("+t+")", str(y))
	@staticmethod
	def get_ellipse_block(width, height, x_low, x_high, y_low, y_high, t="@t*0.01*math.pi"):
		"Returns a moving block with specified width and height whose top-left corner moves in the ellipse defined by the given rectangle."
		return MovingBlock(width, height, "("+str(x_low)+"+"+str(x_high)+")/2 + ("+str(x_high)+"-"+str(x_low)+")/2*math.cos("+t+")", "("+str(y_low)+"+"+str(y_high)+")/2 + ("+str(y_high)+"-"+str(y_low)+")/2*math.sin("+t+")")
	
class Actor(Box):
	STANDARD_SIZE = (24,32)
	def __init__(self, width=24, height=32, color=(255,128,128), border_color=None):
		Box.__init__(self, width, height, color, border_color)
		
		#actor collision state
		self.is_grounded = False		#is touching a solid box that's below
		self.is_left_walled = False		#is touching a solid box on the left
		self.is_right_walled = False	#is touching a solid box on the right
		self.is_left_toe_grounded = False
		self.is_right_toe_grounded = False
										#Note: these are reset to false on each actor update, and reapplied by the collision fixer.
		
		self.wall_stick_time = 0
		self.jumps = 0
		
		self.wall_release_time = 5		#actor will stick to wall for X frames before letting go.
		self.wall_hang_friction = 0.1	#vertical friction actor applies when hanging on a wall.
		self.is_alive = True
		self.is_crushed = False
		self.is_player = False
		self.finished_level = False
		
		self.jump_speed = -7
		self.max_vx = 4		#'run' speed
		self.move_speed = 2 #'dash' speed
		self.air_move_speed = 0.5 #degree of aerial control the player has over the character

	def reset(self):
		self.jumps = 0
		self.wall_stick_time = 0
		self.is_alive = True
		self.is_grounded = False
		self.is_left_walled = False
		self.is_right_walled = False
		self.is_left_toe_grounded = False
		self.is_right_toe_grounded = False
		self.is_crushed = False
		self.finished_level = False
		self.v = (0,0)
		self.a = (0,0.3)
	def jump_action(self):
		if self.is_grounded == False:	#if not grounded, check for walljumps
			if self.is_left_walled:
				self.set_vy(self.jump_speed)
				self.set_vx(-10*self.jump_speed)
				return 
			elif self.is_right_walled:
				self.set_vy(self.jump_speed)
				self.set_vx(10*self.jump_speed)
				return
		
		if self.jumps > 0:	#otherwise use a normal jump (even if not grounded.)
			self.set_vy(self.jump_speed)
			self.jumps = self.jumps - 1
		
	def move_action(self,dir):
		"if dir > 0, moves actor right. If dir < 0 moves left. Otherwise actor will not move."
		
		if self.is_grounded:
			if self.v[0] < self.move_speed and self.v[0] > -self.move_speed: 
				#making a grounded actor immediately dash
				self.v = (self.move_speed*dir, self.v[1])
			self.a = (0.4*dir, self.a[1])
		else:
			if (self.is_left_walled and dir > 0) or (self.is_right_walled and dir < 0):
				if self.wall_stick_time >= self.wall_release_time:
					self.wall_stick_time = 0
					self.set_vx(self.vx() + dir*self.air_move_speed)
				else:
					self.wall_stick_time += 1
			else:
				self.set_vx(self.vx() + dir*self.air_move_speed)
		
	def update(self, dt):
		if not self.is_right_walled and not self.is_left_walled:
			self.wall_stick_time = 0
		if not self.is_grounded:	#if player has left ground, there shouldn't be any horizontal acceleration
			self.set_ax(0)
		
		self.is_grounded = False
		self.is_left_walled = False
		self.is_right_walled = False
		self.is_left_toe_grounded = False
		self.is_right_toe_grounded = False
		
		self.apply_friction(dt)
		Box.update(self,dt)
		
		#fall detection
		if self.y() >= 2048:
			self.is_alive = False
			
	def collided_with(self,obj,dir="NONE"):
		if obj.is_solid:
			if dir == "BOTTOM":
				self.jumps = 1
	def apply_friction(self, dt):
		if (self.is_left_walled or self.is_right_walled) and self.vy() > 0:
			wall_fric = 0.1
			self.set_vy(self.vy()-0.1)
class BadBlock(Block):
	def __init__(self, width, height, color=None, border_color=None):
		color = Block.BAD_COLOR if color == None else color
		Block.__init__(self, width, height, color, border_color)
	def collided_with(self, obj, dir="NONE"):
		if isinstance(obj, Actor):
			obj.is_alive = False
class Switch(Block):
	SWITCH_COLOR = (100,0,200)
	def __init__(self, width=16, height=16, color=None, border_color=(175,175,175)):
		color = Switch.SWITCH_COLOR if color == None else color
		Block.__init__(self,width,height,color,border_color)
		self.dark_color = color
		self.light_color = (self.color[0] + 50, self.color[1] + 50, self.color[2] + 50)
		self.has_physics = False
		self.is_movable = False
		self.is_solid = True
		self.targets = []
		self.currently_light_colored = False
		self.collided_last_update = False
	def update(self, dt):
		Block.update(self,dt)
		if self.currently_light_colored == True and self.collided_last_update == False:
			self.set_color(self.dark_color)
			for thing in self.targets:
				thing.set_color(self.dark_color)
				thing.set_border_color(self.dark_color)
			self.currently_light_colored = False
		self.collided_last_update = False
		
	def collided_with(self, obj, dir="NONE"):
		if isinstance(obj, Actor):
			self.collided_last_update = True
			for thing in self.targets:
				thing.is_paused = False
				if not self.currently_light_colored:
					thing.set_color(self.light_color)
					thing.set_border_color(self.light_color)
			self.set_color(self.light_color)
			self.currently_light_colored = True
	def add_target(self, moving_block):
		moving_block.pause_after_next_update = True
		moving_block.set_border_color(self.color)
		moving_block.set_color(self.color)
		
		self.targets.append(moving_block)
		return self
class Enemy(Actor):
	NORMAL_COLOR = (255,0,255)
	SMART_COLOR = (0,125,125)
	BAD_COLOR = (255,0,0)
	def __init__(self, width, height, color=(255,0,255), border_color=None):
		Actor.__init__(self, width, height, color, border_color)
		self.max_vx = 1
		self.move_speed = 0.5
		self.direction = -1
		self.walks_off_platforms = True
		self.is_stompable = True
	def update(self, dt):
		if not self.is_alive:
			self.kill()
			return;
		if not self.walks_off_platforms and self.is_grounded:
			if (self.direction == -1 and not self.is_left_toe_grounded) or (self.direction == 1 and not self.is_right_toe_grounded):
				self.direction = -1*self.direction
		Actor.update(self, dt)
		
		self.move_action(self.direction)
	def collided_with(self, obj, dir="NONE"):
		Actor.collided_with(self,obj,dir)
		if isinstance(obj,Actor):
			if obj.is_player:
				if self.is_stompable and dir == "TOP":
					self.is_alive = False
					obj.set_vy(obj.jump_speed / 2)
					if obj.jumps == 0:
						obj.jumps = 1
				else:
					obj.is_alive = False
		elif obj.is_solid and (dir == "RIGHT" or dir == "LEFT"):
			self.direction = -self.direction
	@staticmethod
	def get_stupid_walker_enemy(x,y, direction = -1):
		res = Enemy(Actor.STANDARD_SIZE[0], Actor.STANDARD_SIZE[1])
		res.set_xy(x,y)
		res.direction = direction
		res.walks_off_platforms = True
		return res
	@staticmethod
	def get_smart_walker_enemy(x,y,direction=-1):
		res = Enemy.get_stupid_walker_enemy(x,y,direction)
		res.walks_off_platforms = False
		res.color = Enemy.SMART_COLOR
		return res
	@staticmethod
	def get_bad_enemy(x,y,smart=True,direction=-1):
		if smart:
			res = Enemy.get_smart_walker_enemy(x,y,direction)
		else:
			res = Enemy.get_stupid_walker_enemy(x,y,direction)
		res.color = Enemy.BAD_COLOR
		res.is_stompable = False
		return res

class FinishBlock(Block):
	def __init__(self, width=16, height=16, color=(0,255,0), border_color=(0,255,0)):
		Block.__init__(self, width, height, color, border_color)
	def collided_with(self, obj, dir="NONE"):
		if isinstance(obj, Actor):
			obj.finished_level = True
			
class CollisionFixer:
	def __init__(self):
		self.thresh = 0.4
	def solve_collisions(self, group):
		unmovables = pygame.sprite.Group()
		movables = pygame.sprite.Group()
		actors = pygame.sprite.Group()
		
		for sprite in group:
			if sprite.is_solid == False:
				continue
			elif sprite.is_pushable:
				movables.add(sprite)
				if isinstance(sprite, Actor):
					actors.add(sprite)
			else:
				unmovables.add(sprite)
		
		for sprite in movables:	#solving movable-unmovable coliisions
			list = pygame.sprite.spritecollide(sprite,unmovables,False)
			for other in list:
				self.solve_pushout_collision(other, sprite)
		
		for sprite in actors:	#Checking for crushed actors
			list = pygame.sprite.spritecollide(sprite,unmovables,False)
			for obj in list:
				if self.really_intersects(sprite.rect, obj.rect, self.thresh):
					sprite.is_crushed = True
					
		for sprite in actors: #Setting is_grounded, is_left_walled, is_right_walled for each actor
			full_rect = sprite.rect
			bot_rect  = pygame.Rect(full_rect.x,full_rect.bottom,full_rect.width,1).inflate(-full_rect.width*self.thresh,0)	#creating a skinny rect that lies directly underneath the sprite.
			left_rect = pygame.Rect(full_rect.x-1,full_rect.y,1,full_rect.height).inflate(0,-full_rect.height*self.thresh)
			right_rect= pygame.Rect(full_rect.right,full_rect.y,1,full_rect.height).inflate(0,-full_rect.height*self.thresh)
			
			candidates = self.rect_collide(full_rect.inflate(2,2), unmovables)
			
			bot_collisions = self.rect_collide(bot_rect, candidates)
			if len(bot_collisions) > 0:
				sprite.is_grounded = True
				for othersprite in bot_collisions:	#setting toe collision states
					coll = self.rect_intersect(othersprite.rect, bot_rect)
					
					if coll.left == bot_rect.left:
						sprite.is_left_toe_grounded = True
					if coll.right == bot_rect.right:
						sprite.is_right_toe_grounded = True
					if sprite.is_left_toe_grounded and sprite.is_right_toe_grounded:
						break
				
			if len(self.rect_collide(left_rect, candidates)) > 0:
				sprite.is_left_walled = True 
			if len(self.rect_collide(right_rect, candidates)) > 0:
				sprite.is_right_walled = True
		for sprite in movables:	#solving movable-movable collisions
			list = pygame.sprite.spritecollide(sprite,movables,False)
			for other in list:
				if other != sprite:
					dir = self.intersect_dir(other.rect, sprite.rect, 0.2) #thresh set to 0 so that vertical collisions always prevail
					sprite.collided_with(other, dir)
		
		movables.empty()
		unmovables.empty()
		actors.empty()
		
	def solve_pushout_collision(self, unmovable, movable):
		assert unmovable.is_pushable == False and movable.is_pushable == True
		v_box = movable.rect.copy()
		v_box.inflate_ip(-v_box.width * self.thresh,0)
		
		intersect = self.rect_intersect(unmovable.rect, v_box)	#vertical correction
		if intersect != None:
			if intersect.bottom == v_box.bottom:	#collision from bottom
				movable.rect.move_ip(0,-intersect.height)
				if movable.vy() > 0:
					movable.set_vy(0)
				if movable.rf_parent != None:
					movable.rf_parent.remove_from_rf(movable)
				unmovable.add_to_rf(movable)
				movable.collided_with(unmovable, "BOTTOM")
				unmovable.collided_with(movable, "TOP")
			elif intersect.top == v_box.top:		#collision from top
				#print "solving vert collision"
				movable.rect.move_ip(0,intersect.height)
				if movable.vy() < 0:
					movable.set_vy(0)
				movable.collided_with(unmovable, "TOP")
				unmovable.collided_with(movable, "BOTTOM")
				
		h_box = movable.rect.copy()
		h_box.inflate_ip(0,-h_box.height * self.thresh)

		intersect = self.rect_intersect(unmovable.rect, h_box)	#horizontal correction
		if intersect != None:
			if intersect.left == h_box.left:
				movable.rect.move_ip(intersect.width,0)
				movable.set_vx(0)
				movable.set_ax(0)
				movable.collided_with(unmovable, "LEFT")
				unmovable.collided_with(movable, "RIGHT")
			elif intersect.right == h_box.right:
				movable.rect.move_ip(-intersect.width,0)
				movable.set_vx(0)
				movable.set_ax(0)
				movable.collided_with(unmovable, "RIGHT")
				unmovable.collided_with(movable, "LEFT")
		
	def rect_intersect(self, r1, r2):
		if not r1.colliderect(r2):
			return None
		
		left  = max(r1.x, r2.x)
		right = min(r1.x + r1.width, r2.x + r2.width)
		top   = max(r1.y, r2.y)
		bot   = min(r1.y + r1.height, r2.y + r2.height)
		
		return pygame.Rect(left,top,right-left,bot-top)
	def intersect_dir(self, r1, r2, thresh):
		"determines the direction from which r1 collides with r2"
		if not self.really_intersects(r1,r2,thresh):
			return "NONE"
		
		dx = -r1.centerx + r2.centerx
		dy = -r1.centery + r2.centery
		atan = math.atan2(dx, dy)
		
		if atan > math.pi/4 and atan < 3*math.pi/4:		 #is this correct/why is this correct? seems to work...
			return "LEFT"
		elif atan > 3*math.pi/4 or atan < -3*math.pi/4:
			return "BOTTOM"
		elif atan < math.pi/4 and atan > -math.pi/4:
			return "TOP"
		elif atan < -math.pi/4 and atan > -3*math.pi/4:
			return "RIGHT"
		
	def really_intersects(self, movable_rect, unmovable_rect, thresh):
		h_box = movable_rect.copy()
		h_box.inflate_ip(0,-h_box.height * thresh)
		v_box = movable_rect.copy()
		v_box.inflate_ip(-v_box.width * thresh,0)
		
		return self.rect_intersect(h_box,unmovable_rect) != None or self.rect_intersect(v_box,unmovable_rect) != None

	def rect_collide(self, rect, spritegroup):
		"Finds all the sprites in Group (or list) spritegroup that collide with given rect. Returns a list of those sprites."
		#TODO - make better
		list = [sprite for sprite in spritegroup if rect.colliderect(sprite.rect)]
		return list
class ReferenceFrameFixer:
	def __init__(self):
		pass
	def solve_rfs(self, group):
		to_delete = sets.Set()
		for box in group:
			to_delete.clear()
			for kid in box.rf_children:
				if not kid.is_still_rf_child_of(box):
					to_delete.add(kid)
			for kid in to_delete:
				box.remove_from_rf(kid)
		
class Path:
	def __init__(self):
		self.t = 0;
		self.x_fun = Path.null_path
		self.y_fun = Path.null_path
	def step(self, dt):
		self.t += dt
		return (self.x_fun(self.t, 100, 0.01, 0, 0), self.y_fun(self.t, -100, 0.01, 0, 0))
		
	@staticmethod
	def null_path(t, A, B, t_offs, y_offs):
		return 0;
	
	@staticmethod
	def sin_path(t, A, B, t_offs, y_offs):
		"= A*sin(B(t-t_offs)) + y_offs"
		return A*math.sin(B*(t-t_offs)) + y_offs
	@staticmethod
	def cos_path(t, A, B, t_offs, y_offs):
		"A*sin(B(t-t_offs)) + y_offs"
		return A*math.cos(B*(t-t_offs)) + y_offs

class CustomPath(Path):
	def __init__(self, _x_fun, _y_fun):
		Path.__init__(self)
		"Example function: 32*math.sin(@t*0.1) + 30"
		self.x_fun = _x_fun.replace("@t", "self.t")
		self.y_fun = _y_fun.replace("@t", "self.t")
		self.t = 0
	def step(self, dt):
		self.t += dt
		return (eval(self.x_fun), eval(self.y_fun))#lol don't worry about this


class Ghost(pygame.sprite.Sprite):
	def __init__(self, x, y, color=(200,128,128)):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((24,32))
		self.color = color
		self.repaint()
		self.rect = pygame.Rect(x,y,24,32)

	def repaint(self):
		self.image.fill(self.color)
