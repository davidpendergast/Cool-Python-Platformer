#set the level's name
self.level_name = "Introduction"

#add actor to world at position (0,0)
group.add(actor.set_xy(0,0))

group.add(phys_objects.Block(128,288).set_xy(0,128))
group.add(phys_objects.Block(256,192).set_xy(128,224))
group.add(phys_objects.Block(256,192).set_xy(512,288))

#stairs
group.add(phys_objects.Block(64,32).set_xy(864,224))
group.add(phys_objects.Block(64,32).set_xy(1024,160))
group.add(phys_objects.Block(64,32).set_xy(1184,96))

#ground under stairs
group.add(phys_objects.Block(576,128).set_xy(768,352))

#wall next to stairs
group.add(phys_objects.Block(384,448).set_xy(1344,32))

group.add(phys_objects.Block(96,64).set_xy(1824,32))
group.add(phys_objects.Block(96,64).set_xy(2016,32))
group.add(phys_objects.Block(96,64).set_xy(2208,32))
group.add(phys_objects.Block(96,64).set_xy(2464,32))
#add finish block
group.add(phys_objects.FinishBlock(16,16).set_xy(2528,-64))