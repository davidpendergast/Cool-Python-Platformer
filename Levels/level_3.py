#set the level's name
self.level_name = "Bad Blocks"

#add actor to world at position (0,0)
group.add(actor.set_xy(0,0))

#starting block
group.add(phys_objects.Block(352,192).set_xy(0,128))
#bad block
group.add(phys_objects.BadBlock(32,32+16).set_xy(256,64+16))

#lava floor
group.add(phys_objects.BadBlock(416,16).set_xy(352,288+16))
group.add(phys_objects.MovingBlock.get_left_right_block(64,32,320,704,192,"0.004*@t*math.pi"))

#right side of pit
group.add(phys_objects.Block(256,192).set_xy(768,128))

#jump
group.add(phys_objects.BadBlock(64,224).set_xy(1056,96))
group.add(phys_objects.BadBlock(32,192).set_xy(1120,128))
group.add(phys_objects.BadBlock(32,160).set_xy(1152,160))

group.add(phys_objects.BadBlock(128,64).set_xy(1056,-96))
group.add(phys_objects.BadBlock(64,32).set_xy(1120,-32))
group.add(phys_objects.BadBlock(32,32).set_xy(1152,0))

#landing
group.add(phys_objects.Block(96,96).set_xy(1216,224))

group.add(phys_objects.Block(16,96).set_xy(1408,96))
#add finish block
group.add(phys_objects.FinishBlock(16,16).set_xy(1312,64))