from keybindings import *

from gamestate import GameState, GameStateManager

import pygame

import levels
import options
import utilities

SELECTED_COLOR = (255,255,0)
UNSELECTED_COLOR = (255,255,255)
BACKGROUND_COLOR = (0,0,0)

MENU_ICING = 30
TITLE_FONT = options.get_font(60)
NORMAL_TEXT_FONT = options.get_font(30)

class MainMenuState(GameState):
    def __init__(self, settings):
        GameState.__init__(self, settings)
        self.selected_color = SELECTED_COLOR
        self.unselected_color = UNSELECTED_COLOR
        self.background_color = BACKGROUND_COLOR
        self.title_image = self.get_title_text_image(options.title(), options.standard_size()[0] - 2*MENU_ICING)
        self.option_names = ["start full run", "grind single level", "edit levels", "select level pack", "settings"]
        self.option_actions = [
            lambda: self._launch_full_run_mode(),
            lambda: self.state_manager.set_current_state(GameStateManager.SELECT_SINGLE_LEVEL_STATE),
            lambda: self._launch_edit_mode(),
            lambda: None,
            lambda: None
        ]
        self.selected_index = 0
        self.option_text_images = []
        for i in range(0, len(self.option_names)):
            name = self.option_names[i]
            c = self.unselected_color if i != self.selected_index else self.selected_color
            self.option_text_images.append(NORMAL_TEXT_FONT.render(name, True, c))
    
    def _launch_full_run_mode(self):
        self.settings.set_single_level_mode(False)
        self.state_manager.set_current_state(GameStateManager.PLAYING_STATE)
        
    def _launch_edit_mode(self):
        self.settings.set_edit_mode(True)
        self.state_manager.set_current_state(GameStateManager.SELECT_SINGLE_LEVEL_STATE)
        
    def switching_to(self, prev_state_id):
        self.settings.set_edit_mode(False)
        options.set_resizable(False, size=options.standard_size())
        
    def configure_keybindings(self):
        self.keydown_action_map.update({
            MENU_UP: lambda: self.set_selected_index(self.selected_index - 1),
            MENU_DOWN: lambda: self.set_selected_index(self.selected_index + 1),
            MENU_CONFIRM: lambda: self.option_actions[self.selected_index](),
            QUIT: lambda: self._full_exit()
        })
        
    def _full_exit(self):
        self.state_manager.full_quit = True
        
    def handle_event(self, event):
        GameState.handle_event(self, event)
    
    def set_selected_index(self, new_index):
        new_index = new_index % len(self.option_names)
        self.option_text_images[self.selected_index] = NORMAL_TEXT_FONT.render(self.option_names[self.selected_index], True, self.unselected_color)
        self.option_text_images[new_index] = NORMAL_TEXT_FONT.render(self.option_names[new_index], True, self.selected_color)
        self.selected_index = new_index
        
    def update(self, dt):
        pass
        
    def draw(self, screen):
        screen.fill(self.background_color)
        standard_width = options.standard_size()[0]
        standard_height = options.standard_size()[1]
        xoffset = (screen.get_width() - standard_width) / 2
        yoffset = (screen.get_height() - standard_height) / 2
        
        if screen.get_width() > standard_width or screen.get_height() > standard_height:
            # so that in dev mode you can see what the actual screen size would be.
            pygame.draw.rect(screen,(255, 0, 0), pygame.Rect(xoffset,yoffset,standard_width,standard_height), 1)
        
        screen.blit(self.title_image, (xoffset + MENU_ICING, yoffset + MENU_ICING))
        option_heights = [x.get_height() for x in self.option_text_images]
        options_height = sum(option_heights)
        options_width = max([x.get_width() for x in self.option_text_images])
        for i in range(0, len(self.option_text_images)):
            opt = self.option_text_images[i]
            xpos = xoffset + standard_width - options_width - MENU_ICING
            ypos = yoffset + standard_height - options_height + sum(option_heights[0:i]) - MENU_ICING
            screen.blit(opt, (xpos, ypos))
            
        level_pack = self.settings.level_path()
        level_pack_image = NORMAL_TEXT_FONT.render(level_pack, True, self.unselected_color)
        screen.blit(level_pack_image, (xoffset + MENU_ICING, yoffset + self.title_image.get_height() + MENU_ICING))
                
    def get_title_text_image(self, title_str, max_width):
        lines = []
        words = title_str.split(" ")
        start_line = 0
        end_line = 0
        while end_line < len(words):
            text = " ".join(words[start_line:end_line+1])
            image = TITLE_FONT.render(text, True, self.unselected_color)
            if image.get_width() > max_width:
                if start_line == end_line:
                    # word itself is too long, just cram it in there
                    lines.append(image)
                    start_line = end_line + 1
                    end_line = end_line + 1
                else:
                    # line is one word too wide
                    text = " ".join(words[start_line:end_line])
                    image = TITLE_FONT.render(text, True, self.unselected_color)
                    lines.append(image)
                    start_line = end_line
            else:
                end_line += 1
        if start_line < end_line:
            text = " ".join(words[start_line:end_line])
            image = TITLE_FONT.render(text, True, self.unselected_color)
            lines.append(image)
            
        total_height = sum([x.get_height() for x in lines])
        total_width = max([x.get_width() for x in lines])
        result = pygame.Surface((total_width, total_height))
        
        y = 0
        for line in lines:
            result.blit(line, (0, y))
            y += line.get_height()
        
        return result
        
class SelectSingleLevelState(GameState):
    def __init__(self, settings):
        GameState.__init__(self, settings)
        self.selected_color = SELECTED_COLOR
        self.unselected_color = UNSELECTED_COLOR
        self.background_color = BACKGROUND_COLOR
        self.refresh_ui()
        
    def refresh_ui(self):
        self.loaded_levels = self._fetch_levels()
        self.selected_index = 0
        self.num_levels = len(self.loaded_levels)
        self.option_names = [utilities.extend_to(x.num, 6) + x.name for x in self.loaded_levels]
        self.option_actions = [(lambda i: self.launch_single_level_mode(i)) for i in range(0, self.num_levels)]
        self.option_images = [self._get_option_image(i) for i in range(0, self.num_levels)]
            
    def _get_option_image(self, index):
        name = self.option_names[index]
        c = self.unselected_color if index != self.selected_index else self.selected_color
        return NORMAL_TEXT_FONT.render(name, True, c)
        
    def launch_single_level_mode(self):
        self.settings.set_single_level_num(self.selected_index)
        self.settings.set_single_level_mode(True)
        
        self.state_manager.set_current_state(GameStateManager.PLAYING_STATE)
    
    def _fetch_levels(self):
        level_manager = levels.LevelManager(self.settings)
        result = []
        for i in range(0, level_manager.get_num_levels()):
            level_manager.load_level(i)
            result.append(level_manager.current_level)
        return result
    
    def draw(self, screen):
        screen.fill(self.background_color)
        standard_width = options.standard_size()[0]
        standard_height = options.standard_size()[1]
        xoffset = (screen.get_width() - standard_width) / 2
        yoffset = (screen.get_height() - standard_height) / 2
        
        if screen.get_width() > standard_width or screen.get_height() > standard_height:
            # so that in dev mode you can see what the actual screen size would be.
            pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(xoffset,yoffset,standard_width,standard_height), 1)
        
        y = 0
        for option in self.option_images:
            screen.blit(option, (xoffset + MENU_ICING, yoffset + y + MENU_ICING))
            y += option.get_height()
            
    def set_selected_index(self, new_index):
        new_index = new_index % self.num_levels
        if new_index != self.selected_index:
            old_index = self.selected_index
            self.selected_index = new_index
            self.option_images[old_index] = self._get_option_image(old_index)
            self.option_images[new_index] = self._get_option_image(new_index)
        
        
    def configure_keybindings(self):
        self.keydown_action_map.update({
            MENU_UP: lambda: self.set_selected_index(self.selected_index - 1),
            MENU_DOWN: lambda: self.set_selected_index(self.selected_index + 1),
            MENU_CONFIRM: lambda: self.launch_single_level_mode(),
            QUIT: lambda: self.state_manager.set_current_state(GameStateManager.MAIN_MENU_STATE),
        })
