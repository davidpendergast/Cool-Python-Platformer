from keybindings import *

import pygame
import json
import os

from gamestate import GameState, GameStateManager
from playingstate import InGameState
import blocks, actors
import drawing
import levels
import utilities

class EditingState(InGameState):
    SELECTED_COLOR = (255, 128, 255)
    output_dir = "saved_levels"
    def __init__(self, settings, platformer_instance):
        InGameState.__init__(self, settings, platformer_instance)
        self.selected = None
        self.selected_old_color = None
        
        # used to alternate which block gets selected if user clicks on an overlapping position
        self._last_clicked_objs = []
        self._last_idx_used = -1
        
        self._mouse_down_pos = None
        
    def pre_event_update(self):
        pass
        
    def configure_keybindings(self):
        InGameState.configure_keybindings(self)

        self.keydown_action_map.update({
            CAMERA_UP:              lambda: self.set_keystate("up", True), 
            CAMERA_LEFT:            lambda: self.set_keystate("left", True), 
            CAMERA_RIGHT:           lambda: self.set_keystate("right", True), 
            CAMERA_DOWN:            lambda: self.set_keystate("down", True), 
            RESIZE_LEFT:            lambda: self.resize_selected(-self._val(), 0),
            RESIZE_UP:              lambda: self.resize_selected(0, -self._val()),
            RESIZE_RIGHT:           lambda: self.resize_selected(self._val(), 0),
            RESIZE_DOWN:            lambda: self.resize_selected(0, self._val()),
            TRANSLATE_LEFT:         lambda: self.move_selected(-self._val(), 0),
            TRANSLATE_UP:           lambda: self.move_selected(0, -self._val()),
            TRANSLATE_RIGHT:        lambda: self.move_selected(self._val(), 0),
            TRANSLATE_DOWN:         lambda: self.move_selected(0, self._val()),
            TOGGLE_EDIT_MODE:       lambda: self.state_manager.set_current_state(GameStateManager.PLAYING_STATE),
            SAVE_LEVEL:             lambda: self.do_save(),
            DUPLICATE_SELECTED:     lambda: self.duplicate_selected(),
            CYCLE_SELECTED_TYPE:    lambda: self.cylcle_type_of_selected(),
            DELETE_SELECTED:        lambda: self.delete_selected()
        })
        self.keyup_action_map.update({
            CAMERA_UP:      lambda: self.set_keystate("up", False), 
            CAMERA_LEFT:    lambda: self.set_keystate("left", False), 
            CAMERA_RIGHT:   lambda: self.set_keystate("right", False), 
            CAMERA_DOWN:    lambda: self.set_keystate("down", False), 
        })
        
    def _val(self):
        return 4 if self.keystate["shift"] else 32
    
    def handle_event(self, event):
        InGameState.handle_event(self, event)
        if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP:
            x, y = self.get_drawer().screen_to_game_position((event.pos[0], event.pos[1]), snap_to_grid=False)
            grid_x, grid_y = self.get_drawer().screen_to_game_position((event.pos[0], event.pos[1]), snap_to_grid=True)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._mouse_down_pos = (grid_x, grid_y)
            elif event.type == pygame.MOUSEBUTTONUP:
                # using grid position values to prevent tiny drag annoyances
                if self._mouse_down_pos == None or (grid_x, grid_y) == self._mouse_down_pos:
                    utilities.log("Click at: ("+str(x)+", "+str(y)+") ["+str(grid_x)+", "+str(grid_y)+"]")
                    self._click_and_release_at(x,y)
                else:
                    x1 = self._mouse_down_pos[0]
                    y1 = self._mouse_down_pos[1]
                    x2 = grid_x
                    y2 = grid_y
                    xavg = (x1 + x2) / 2
                    yavg = (y1 + y2) / 2
                    utilities.log("Drag from: ["+str(x1)+", "+str(y1)+"] to ["+str(x2)+", "+str(y2)+"]")
                    x_path_str = str(xavg)+" + "+str((x2 - x1) / 2)+"*cos(t*0.03)"
                    y_path_str = str(yavg)+" + "+str((y2 - y1) / 2)+"*sin(t*0.03)"
                    path_json_str = "\"path\": {\"type\": \"path\", \"x_path\": \""+x_path_str+"\", \"y_path\": \""+y_path_str+"\"}"
                    utilities.log(path_json_str)
            
    def _click_and_release_at(self, x, y):
        clicked_objs = self.get_level_manager().current_level.get_objects_at((x,y))
        if len(clicked_objs) > 0:
            if set(self._last_clicked_objs) == set(clicked_objs):
                next_index = (self._last_idx_used + 1) % len(self._last_clicked_objs)
                self.set_selected(self._last_clicked_objs[next_index])
                self._last_idx_used = next_index
            else:
                self.set_selected(clicked_objs[0])
                self._last_clicked_objs = clicked_objs
                self._last_idx_used = 0
        else:
            self.set_selected(None)
                
    def update(self, dt):
        self.do_camera_move(dt)
        
        if self.settings.frozen_mode():
            dt = 0
        
        for item in self.get_entities():
            if item is not self.get_player():
                item.update(dt)
        
        self.platformer_instance.current_level().bring_out_yer_dead()
    
    def do_save(self):   
        num = self.get_level_num()
        filename = self.get_current_level().filename
        utilities.log("Overwriting " + filename + "...")
        curr_json = self.get_current_level().to_json()
        
        with open(filename, 'w') as outfile:
            json_string = utilities.level_json_to_string(curr_json)
            utilities.log("writing text:\n" + json_string)
            outfile.write(json_string)
        utilities.log("done.")
    
    def do_camera_move(self, dt):
        if bool(self.keystate['left']) ^ bool(self.keystate['right']):
            if self.keystate['left']: 
                self.get_drawer().move_camera(-4, 0)
            elif self.keystate['right']: 
                self.get_drawer().move_camera(4, 0)
        
        if bool(self.keystate['up']) ^ bool(self.keystate['down']):
            if self.keystate['up']: 
                self.get_drawer().move_camera(0, -4)
            elif self.keystate['down']: 
                self.get_drawer().move_camera(0, 4)
        
    def draw(self, screen):
        self.get_drawer().draw_level(screen, self.get_current_level())
        if self.selected != None:
            self.get_drawer().draw_entities(screen, [self.selected])
        
    def switching_from(self, new_state_id):
        self.set_selected(None)
        
    def set_selected(self, obj):
        if self.selected != None:
            self.selected.set_color(self.selected_old_color)
            self.selected_old_color = None
        
        self.selected = obj
        
        if self.selected != None:
            utilities.log(str(self.selected) + " selected!")
            self.selected_old_color = self.selected.color
            self.selected.set_color(EditingState.SELECTED_COLOR)
            
    def delete_selected(self):
        if self.selected != None:
            utilities.log("deleting "+str(self.selected))
            self.get_current_level().remove_object(self.selected)
            self.set_selected(None)
            
    def resize_selected(self, width_expand, height_expand):
        if self.selected != None:
            utilities.log("stretching "+str(self.selected)+" by "+str(width_expand)+", "+str(height_expand))
            width = self.selected.width()
            height = self.selected.height()
            self.selected.set_size(max(8, width + width_expand), max(8, height + height_expand))
            
    def move_selected(self, x_move, y_move):
        if self.selected != None:
            utilities.log("moving "+str(self.selected)+" by "+str(x_move)+", "+str(y_move))
            self.selected.set_xy(self.selected.x() + x_move, self.selected.y() + y_move)
            
    def duplicate_selected(self):
        if self.selected != None:
            utilities.log("duplicating "+str(self.selected))
            if self.selected.is_block():
                selected_json = self.selected.to_json()
                new_entity = blocks.BlockFactory.from_json(selected_json)
                self.get_current_level().add_object(new_entity)
            elif self.selected.is_spawn_point():
                selected_json = self.selected.to_json()
                new_spawn = actors.SpawnPoint.from_json(selected_json)
                self.get_current_level().spawn_list.append(new_spawn) # this should be ok
            else:
                entities.log("Cannot dupe entity type: "+str(self.selected))
                
    def cylcle_type_of_selected(self):
        if self.selected != None:
            if self.selected.is_block() and not self.selected.is_moving_block(): ## can't deal with moving blocks yet
                utilities.log("Changing type of "+str(self.selected))
                types = ["normal", "bad", "finish"]
                selected_json = self.selected.to_json()
                curr_type_idx = types.index(selected_json["type"])
                if curr_type_idx == -1:
                    utilities.log("unrecognized type: "+str(selected_json["type"]))
                else:
                    selected_json["type"] = types[(curr_type_idx + 1) % len(types)]
                    new_entity = blocks.BlockFactory.from_json(selected_json)
                    
                    self.get_current_level().remove_object(self.selected)
                    self.get_current_level().add_object(new_entity)
                    self.set_selected(new_entity)
            else:
                utilities.log("Can't change type of entity: "+str(self.selected))
                
