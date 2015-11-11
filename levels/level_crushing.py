self.level_name = "Working Title=Smashing Crushes"
group.add(actor.set_xy(0,-64))
group.add(phys_objects.Block(640,40*32).set_xy(0,0))
group.add(phys_objects.Block(640,40*32).set_xy(0,-40*32-7*32))
group.add(phys_objects.MovingBlock.get_up_down_block(320,7*32,96,-224,-64))

group.add(phys_objects.MovingBlock.get_up_down_block(32,40*32,768,-64,-64+128))
group.add(phys_objects.Block(32,40*32).set_xy(768,-64 - 40*32))

group.add(phys_objects.MovingBlock.get_up_down_block(32,40*32,928,0,0+128))
group.add(phys_objects.Block(32,40*32).set_xy(928,0 - 40*32))