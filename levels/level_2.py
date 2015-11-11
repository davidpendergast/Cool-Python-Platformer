#set the level's name
self.level_name = "Walljumping"

#add actor to world at position (0,0)
group.add(actor.set_xy(0,0))

#starting ground
group.add(phys_objects.Block(544,192).set_xy(0,128))
#first wall
group.add(phys_objects.Block(64,384).set_xy(544,-64))
#small platform
group.add(phys_objects.Block(64,16).set_xy(416,0))
#flat platform off first wall
group.add(phys_objects.Block(256,64).set_xy(608,-64))

#big block, 2nd wall jump
group.add(phys_objects.Block(320,288).set_xy(928,-160))

group.add(phys_objects.Block(64,128).set_xy(800,0))
group.add(phys_objects.Block(64,64).set_xy(864,64))

#pipe
group.add(phys_objects.Block(16,224).set_xy(1216+16,-384))
group.add(phys_objects.Block(16,288).set_xy(1152,-512))

#room
group.add(phys_objects.Block(160,64).set_xy(1248,-384))
group.add(phys_objects.Block(256,32).set_xy(1152,-544))
group.add(phys_objects.Block(32,128).set_xy(1376,-512))


#add finish block
group.add(phys_objects.FinishBlock(16,16).set_xy(1312,-512))