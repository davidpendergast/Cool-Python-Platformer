#set the level's name
self.level_name = "Template Level"

#add actor to world at position (0,0)
group.add(actor.set_xy(0,0))

#add a block with width=128, height=32, position=(32,128)
group.add(phys_objects.Block(128,32).set_xy(0,128))

#add finish block
group.add(phys_objects.FinishBlock(16,16).set_xy(128,128))