import utilities

## in-game commands
JUMP = "jump"
MOVE_LEFT = "move_left"
MOVE_RIGHT = "move_right"
PLAYER_MOVES = [JUMP, MOVE_LEFT, MOVE_RIGHT]

TAKE_SCREENSHOT = "screenshot"
QUIT = "quit"
PAUSE = "pause"

# level editor commands
SAVE_LEVEL = "save_level"
DUPLICATE_SELECTED = "duplicated_selected"
CYCLE_SELECTED_TYPE = "cycle_selected_type"
DELETE_SELECTED = "delete_selected"

CAMERA_UP = "edit_mode_camera_up"
CAMERA_LEFT = "edit_mode_camera_left"
CAMERA_RIGHT = "edit_mode_camera_right"
CAMERA_DOWN = "edit_mode_camera_down"
CAMERA_DIRS = [CAMERA_UP, CAMERA_DOWN, CAMERA_RIGHT, CAMERA_LEFT]

RESIZE_LEFT = "edit_mode_expand_left"
RESIZE_UP = "edit_mode_expand_up"
RESIZE_RIGHT = "edit_mode_expand_right"
RESIZE_DOWN = "edit_mode_expand_down"
RESIZE_DIRS = [RESIZE_UP, RESIZE_DOWN, RESIZE_RIGHT, RESIZE_LEFT]

TRANSLATE_LEFT = "edit_mode_move_left"
TRANSLATE_UP = "edit_mode_move_up"
TRANSLATE_RIGHT = "edit_mode_move_right"
TRANSLATE_DOWN = "edit_mode_move_down"
TRANSLATE_DIRS = [TRANSLATE_UP, TRANSLATE_DOWN, TRANSLATE_RIGHT, TRANSLATE_LEFT]
TOGGLE_EDIT_MODE = "toggle_edit_mode"

# menu commands
MENU_UP = "menu_up"
MENU_DOWN = "menu_down"
MENU_LEFT = "menu_left"
MENU_RIGHT = "menu_right"
MENU_DIRS = [MENU_UP, MENU_DOWN, MENU_RIGHT, MENU_LEFT]
MENU_CONFIRM = "menu_confirm"

RESET_LEVEL = "reset_level"
RESET_LEVEL_SOFT = "reset_level_soft"
RESET_RUN = "reset_run"
PREVIOUS_LEVEL = "previous_level"
NEXT_LEVEL = "next_level"

SHOW_GRID = "show_grid"
INVINCIBLE_MODE = "invincible_mode"
FREEZE_MODE = "freeze_mode"

SHIFT = "shift"
CTRL = "ctrl"

class KeyBindings:
    def __init__(self, action_list, settings):
        self.settings = settings
        self.action_map = {}
        self.add_actions(action_list)
    
    def has_binding(self, key):
        return key in self.action_map
        
    def get_action(self, key):
        if key in self.action_map:
            return self.action_map[key]
    
    def add_actions(self, action_list):
        for action in action_list:
            self.add_action(action)
        
    def add_action(self, action):
        bindings = self.settings.get_keybinding(action)
        if bindings == None or len(bindings) == 0:
            utilities.log("WARN: action not bound to key: "+action)
        else:
            for key in bindings:
                if key in self.action_map:
                    utilities.log("WARN: actions ("+str(action)+", "+str(self.action_map[key])+") bound to same key: "+str(key))
                else:
                    self.action_map[key] = action
