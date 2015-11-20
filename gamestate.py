import pygame
import sys
import phys_objects

class Game:
    def __init__(self):
        self.group = pygame.sprite.Group()
        self.actor = phys_objects.Actor(24, 32, (128, 128, 255))
        self.actor.is_player = True
        self.level_num = 0
        self.death_count = 0
        self.level_name = None
        self.total_time = 0
        self.level_time = 0
        self.level_manager = LevelManager("levels")
        self.level_manager.load_level(0, self.actor, self.group)
        
    def add_time(self):
        self.total_time += 1
        self.level_time += 1
        
    def reset_level(self):
        self.actor.reset()
        self.level_manager.load_level(self.level_num, self.actor, self.group)
        
    def next_level(self, update_highscore=False):
        if update_highscore:
            self.level_manager.update_level_highscore(self.level_num, self.level_time)
            
        if self.level_num == self.level_manager.get_num_levels() - 1:
            self.level_manager.update_total_time_highscore(self.total_time)
            self.level_manager.write_header()
            print "Game Over!"
            
            # TEMPORARY - loop back to level 0
            self.level_num = 0
            self.level_time = 0
            self.total_time = 0
            self.actor.reset()
            self.level_manager.load_level(self.level_num, self.actor, self.group)
        else:   
            self.level_num += 1
            self.level_time = 0
            self.actor.reset()
            self.level_manager.load_level(self.level_num, self.actor, self.group)
            
    def prev_level(self):
        if self.level_num > 0:
            self.level_num += -1
        self.actor.reset()
        self.level_manager.load_level(self.level_num, self.actor, self.group)
        
    def draw_gui(self, screen):
        font = pygame.font.Font(None, 36)
        level_text = font.render("Level: "+str(self.level_num + 1), True, (255, 255, 255))
        level_title = font.render(str(self.level_manager.level_name), True, (255, 255, 255))
        death_text = font.render("Deaths: "+str(self.death_count), True, (255, 255, 255))
        text_height = level_text.get_height()
        
        time_text = font.render("Time: " + Game.format_time_string(self.total_time), True, (255, 255, 255))
        screen.blit(level_text, (0, 0))
        screen.blit(level_title, (0, text_height))
        screen.blit(time_text, (screen.get_width()/2 - time_text.get_width()/2, 0))
        screen.blit(death_text, (screen.get_width() - death_text.get_width(), 0))
        
    @staticmethod
    def format_time_string(time):
        if time % 60 < 10:
            seconds = "0" + str(time % 60)
        else:
            seconds = str(time % 60)
        return str(time // 60) + ":" + seconds
    def draw_background(self):
        pass
        
        
class LevelManager:
    def __init__(self, file_dir):
        self.level_num = 0
        self.actor = None
        self.group = None
        self.level_name = None      # accessed in level files, do not change
        
        self.file_dir = file_dir    # "Levels", most likely
        self.level_filenames =[]
        self.level_highscore_data = []
        self.read_header()
        
    def get_num_levels(self):
        return len(self.level_filenames)
        
    def load_level(self, num, actor, group):
        assert num >= 0 and num < len(self.level_filenames)
        group.empty()
        self.group = group
        self.level_num = num
        self.actor = actor
        self.level_name = "<Unnamed>"
            
        file_name = self.file_dir + "/" + self.level_filenames[num]+".py"
        print "exec-ing " + file_name
        try:
            execfile(file_name)
        except IOError:
            print file_name+" could not be loaded. Please ensure that the file exists and is properly named."
            self.load_void_level(actor, group)
        except:
            print file_name+" threw unexpected error while loading:", sys.exc_info()[0]
            self.load_void_level(actor, group)
            
    def update_level_highscore(self, level_num, time):
        if len(self.level_highscore_data)-1 <= level_num:
            print "Error, could not update high score of level "+str(level_num)
        else:
            print "old time = "+str(self.level_highscore_data[level_num][0])+", new time = "+str(time)
            if self.level_highscore_data[level_num][0] > time:
                print "New High Score!"
                self.level_highscore_data[level_num] = (time, "DLP")
    
    def update_total_time_highscore(self, time):
        print "Total time = " + str(time)
        if self.level_highscore_data[-1][0] > time:
            print "New High Score!"
            self.level_highscore_data[-1] = (time, "DLP");
                
    def load_void_level(self, actor, group):
        group.empty()
        self.group = group
        self.level_num = -2
        self.actor = actor
        self.level_name = "The Void"
        group.add(actor.set_xy(0, 0))
        group.add(phys_objects.Block(128, 128).set_xy(0, 128))
        group.add(phys_objects.FinishBlock(16, 16).set_xy(56, -64))
        
    def read_header(self):
        header = open(self.file_dir + "/header.txt")
        header_txt = header.read()
        print header_txt
        header_lines = header_txt.splitlines()
        i = 0
        while header_lines[i] is '':    # skip opening whitespace
            i += 1
        line = header_lines[i].split("\t")
        print str(line[0])
        if line[0] == "@levels":        # reading level filenames
            i += 1
            while header_lines[i] is not '':        
                line = header_lines[i].split("\t")
                self.level_filenames.append(line[0])
                i += 1
        while header_lines[i] is '':    # skip inbetween whitespace
            i += 1
        line = header_lines[i].split("\t")
        if line[0] == "@highscores":    # read high score info
            i += 1
            while i < len(header_lines) and header_lines[i] is not '':
                line = header_lines[i].split("\t")
                self.level_highscore_data.append((int(line[1]), line[2]))
                i += 1
        print str(self.level_filenames)
        print str(self.level_highscore_data)
        
    def write_header(self):
        header = open(self.file_dir + "/header.txt", 'w')
        header.flush()
        header.write("@levels\t(filename)\n")
        
        for line in self.level_filenames:
            header.write(line + "\n")
        
        header.write("\n@highscores (level, time, initials, formatted time)\n")
        
        for i in range(0, len(self.level_highscore_data)):
            line = self.level_highscore_data[i]
            i_str = str(i) if i < len(self.level_highscore_data)-1 else "ALL"
            header.write(i_str + "\t" + str(line[0]) + "\t" + line[1] +"\t" + Game.format_time_string(line[0]) + "\n")
            
        header.close()
        
            
            
            
            
            
            