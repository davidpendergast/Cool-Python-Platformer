#self.level_name = "Enemies 101"
#group.add(actor.set_xy(0,0))
#group.add(phys_objects.Block(544,32).set_xy(0,224))

#group.add(phys_objects.Enemy.get_stupid_walker_enemy(704,-64))
#group.add(phys_objects.Enemy.get_smart_walker_enemy(544,-32,1))
#group.add(phys_objects.MovingBlock.get_up_down_block(64, 16, 544, 224, 0, t="@t*0.01*math.pi"))
#group.add(phys_objects.Block(128,256).set_xy(608,0))
#group.add(phys_objects.Enemy.get_bad_enemy(416,160,True))
#for i in range(0,8):
	#group.add(phys_objects.MovingBlock.get_ellipse_block(64, 16, 736, 1280, 192, -192, t="-@t*0.005*math.pi + 2*math.pi*"+str(i)+"/8"))
			
#set the level's name
self.level_name = "Moving Platforms"

#add actor to world at position (0,0)
group.add(actor.set_xy(0,0))

#start block
group.add(phys_objects.Block(256,192).set_xy(0,128))
#nub
group.add(phys_objects.Block(32,64).set_xy(256,192))
#ground
group.add(phys_objects.Block(256,64).set_xy(256,256))
group.add(phys_objects.MovingBlock.get_left_right_block(64,16,256,448,128))
#wall
group.add(phys_objects.Block(128,256).set_xy(512,64))

group.add(phys_objects.MovingBlock.get_up_down_block(64,16,736,-64,160))

group.add(phys_objects.Block(128,384).set_xy(896,-64))
group.add(phys_objects.MovingBlock.get_left_right_block(64,16,1024,1024+256,-64))
group.add(phys_objects.MovingBlock.get_up_down_block(64,16,1344,-256,-64))

#add finish block
group.add(phys_objects.FinishBlock(16,16).set_xy(1376,-352))
