self.level_name = "Waves"
actor.set_xy(0,0)
wall1 = phys_objects.Block(128, 256)
wall1.set_xy(0,128)

bad = phys_objects.BadBlock(512,8)
bad.set_xy(128,128+64)

group.add(wall1,bad)

for i in range(0,16):
	m1 = phys_objects.MovingBlock.get_up_down_block(32,32,128+i*32,128,256+128-32,"-@t*0.01*math.pi+"+str(i)+"*math.pi/8")
	group.add(m1)

for i in range(0,16):
	m1 = phys_objects.MovingBlock.get_up_down_block(32,32,+16*32+128 + 128+i*32,128,256+128-32,"-@t*0.01*math.pi+"+str(i)+"*math.pi/8")
	group.add(m1)
	
bad2 = phys_objects.BadBlock(512-32,8)
bad2.set_xy(256+512,128+64)

b = phys_objects.BadBlock(8,192+8)
b.set_xy(768-8,0)
group.add(b)

f = phys_objects.FinishBlock(16,16)
f.set_xy(832,64)
group.add(f)

group.add(bad2,actor)