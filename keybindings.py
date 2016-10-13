import utilities

ALL_ACTIONS = []
def register(action_id):
    ALL_ACTIONS.append(action_id)
    return action_id
    
## in-game commands
JUMP            = register("jump")
MOVE_LEFT       = register("move_left")
MOVE_RIGHT      = register("move_right")
PLAYER_MOVES    = [JUMP, MOVE_LEFT, MOVE_RIGHT]

TAKE_SCREENSHOT = register("screenshot")
QUIT            = register("quit")
PAUSE           = register("pause")

# level editor commands
SAVE_LEVEL          = register("save_level")
DUPLICATE_SELECTED  = register("duplicated_selected")
CYCLE_SELECTED_TYPE = register("cycle_selected_type")
DELETE_SELECTED     = register("delete_selected")

CAMERA_UP       = register("edit_mode_camera_up")
CAMERA_LEFT     = register("edit_mode_camera_left")
CAMERA_RIGHT    = register("edit_mode_camera_right")
CAMERA_DOWN     = register("edit_mode_camera_down")
CAMERA_DIRS     = [CAMERA_UP, CAMERA_DOWN, CAMERA_RIGHT, CAMERA_LEFT]

RESIZE_LEFT     = register("edit_mode_expand_left")
RESIZE_UP       = register("edit_mode_expand_up")
RESIZE_RIGHT    = register("edit_mode_expand_right")
RESIZE_DOWN     = register("edit_mode_expand_down")
RESIZE_DIRS     = [RESIZE_UP, RESIZE_DOWN, RESIZE_RIGHT, RESIZE_LEFT]

TRANSLATE_LEFT  = register("edit_mode_move_left")
TRANSLATE_UP    = register("edit_mode_move_up")
TRANSLATE_RIGHT = register("edit_mode_move_right")
TRANSLATE_DOWN  = register("edit_mode_move_down")
TRANSLATE_DIRS  = [TRANSLATE_UP, TRANSLATE_DOWN, TRANSLATE_RIGHT, TRANSLATE_LEFT]
TOGGLE_EDIT_MODE = register("toggle_edit_mode")

# menu commands
MENU_UP         = register("menu_up")
MENU_DOWN       = register("menu_down")
MENU_LEFT       = register("menu_left")
MENU_RIGHT      = register("menu_right")
MENU_DIRS       = [MENU_UP, MENU_DOWN, MENU_RIGHT, MENU_LEFT]
MENU_CONFIRM    = register("menu_confirm")

RESET_LEVEL     = register("reset_level")
RESET_LEVEL_SOFT = register("reset_level_soft")
RESET_RUN       = register("reset_run")
PREVIOUS_LEVEL  = register("previous_level")
NEXT_LEVEL      = register("next_level")

SHOW_GRID       = register("show_grid")
INVINCIBLE_MODE = register("invincible_mode")
FREEZE_MODE     = register("freeze_mode")

SHIFT           = register("shift")
CTRL            = register("ctrl")

class KeyBindings:
    def __init__(self, settings):
        self.settings = settings
        self.action_map = {}
        self._build_map()
    
    def has_actions_for_key(self, key):
        return key in self.action_map and len(self.action_map[key]) > 0
    
    def get_actions_for_key(self, key):
        "gets all the actions mapped to given key"
        if key in self.action_map:
            return self.action_map[key]
        else:
            return []
            
    def _build_map(self):
        for action in ALL_ACTIONS:
            bindings = self.settings.get_keybinding(action)
            if bindings == None or len(bindings) == 0:
                utilities.log("WARN: action not bound to key: "+action)
            else:
                for key in bindings:
                    if key in self.action_map:
                        self.action_map[key].append(action)
                    else:
                        self.action_map[key] = [action]
