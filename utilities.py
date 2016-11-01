from collections import OrderedDict

import random
import re
import options
import json
import os
import pygame

def format_time(ticks):
    "75 -> '1:15'"
    if ticks == None:
        return None
    millis = int(ticks_to_millis(ticks) + 0.5)
    
    secs = str(millis // 1000)
    millis = str(millis % 1000)
    millis = pad_to_length(millis, length=3, filler='0', to_front=True)
    
    return secs + ":" + millis


# This is getting nuked as soon as in-game high score viewing is implemented
def unformat_time(time_str):
    "'1:15' -> 75"
    if time_str == None:
        return None
    split = time_str.split(":")
    if len(split) == 2:
        millis = int(split[0])*1000 + int(split[1])
        return int(millis_to_ticks(millis)+0.5)
    else:
        raise ValueError("invalid time string to unformat: "+str(time_str))
        

def lim(x, minimum, maximum):
    return min(max(x, minimum), maximum)
    
def darker(color, amount):
    r = lim(color[0] - amount, 0, 255)
    g = lim(color[1] - amount, 0, 255)
    b = lim(color[2] - amount, 0, 255)
    return (r,g,b)

def lighter(color, amount):
    return darker(color, -amount)
    
def perturb_color(orig_color, max_perturb, only_greyscale):
    sign = (-1,1)
    if only_greyscale:
        val = sign[random.randint(0,1)]*random.randint(0,max_perturb)
        pert = val, val, val
    else:
        pert = [sign[random.randint(0,1)]*random.randint(0,max_perturb) for i in range(3)]

    res = tuple([lim(orig_color[i]+pert[i], 0, 255) for i in range(3)])

    return res

def ticks_to_millis(ticks):
    return (1000 * ticks) / float(options.fps())

def millis_to_ticks(millis):
    return (millis * options.fps()) / float(1000)

def pad_to_length(string, length, filler, to_front=False):
    if len(string) >= length:
        return string
    else:
        pad = length - len(string)
        if to_front:
            return filler*pad + string
        else:
            return string + filler*pad

paren_dict = {
    "(":")",
    "[":"]",
    "{":"}"
}

def make_json_pretty(json_string, _nuke_it=True):
    "removes newlines between elements of innermost lists."
    m = re.search('[({[]', json_string)    
    if m == None:
        if _nuke_it:
            # json_string has no inner list
            return re.sub("\s*,\s*", ", ", json_string)
    else:
        i = m.start(0)
        j = find_close_paren(json_string, i, json_string[i], paren_dict[json_string[i]])
        substring = make_json_pretty(json_string[i+1:j], True)
        
        return json_string[:i+1] + substring + make_json_pretty(json_string[j:], False)
                
    return json_string
    
KEY_ORDER = ["info", "spawns", "blocks", "themes"]                      # main sections
KEY_ORDER = KEY_ORDER + ["name", "version"]                             # info fields
KEY_ORDER = KEY_ORDER + ["type", "x", "y", "path", "width", "height"]   # block attributes
KEY_ORDER = KEY_ORDER + ["x_points", "x_path", "y_points", "y_path", "speed", "offset"] # path stuff
KEY_COMPARE_DICT = {key: KEY_ORDER.index(key) for key in KEY_ORDER}

def key_cmp(key1, key2):
    KEY_COMPARE_DICT.setdefault(key1, -1)
    KEY_COMPARE_DICT.setdefault(key2, -1)
    
    return KEY_COMPARE_DICT[key1] - KEY_COMPARE_DICT[key2]
    

def level_json_to_string(json_data, indent_spaces=4, sort_the_keys=True):
    if sort_the_keys:
        json_data = _sort_keys_recursively(json_data)
        
    result = "{" 
    keys =  json_data.keys()
    for top_level_key in keys:
        value = json_data[top_level_key]
        result += "\n"+(" "*indent_spaces)+"\""+top_level_key+"\": "
        
        if isinstance(value, list):
            result += "["
            value_list = value
            for element in value_list:
                elem_str = json.dumps(element)
                result += "\n"+(" "*2*indent_spaces)+elem_str+","
            if result[-1] == ",":
                result = result[0:len(result)-1]
            if len(value) > 0:
                result += "\n"+(" "*indent_spaces)
            result += "],"
        elif isinstance(value, dict):
            result += "{"
            value_keys = value.keys()
            for key in value_keys:
                result += "\n"+(" "*2*indent_spaces)+"\""+key+"\":"+json.dumps(value[key])+","
            if result[-1] == ",":
                result = result[0:len(result)-1] 
            if len(value) > 0:
                result += "\n"+(" "*indent_spaces)
            result += "},"
        else:
            # just a single atom
            result += json.dumps(value)+","
    if result[-1] == ",":
        result = result[0:len(result)-1]
    if result != "{":
        result += "\n"
    
    return result + "}"
        
def _sort_keys_recursively(json_item):
    "replaces all nested dictionaries with sorted ordered dictionaries"
    if isinstance(json_item, list):
        return [_sort_keys_recursively(x) for x in json_item]
    elif isinstance(json_item, dict):
        return OrderedDict((key, _sort_keys_recursively(json_item[key])) for key in sorted(json_item.keys(), cmp=key_cmp))
    else:
        return json_item
    
def is_collection(json_element):
    return isinstance(json_element, list) or isinstance(json_element, dict)
    
def _paren_for(json_collection, open):
    if isinstance(json_collection, list):
        return "[" if open else "]"
    elif isinstance(json_collection, dict):
        return "{" if open else "}"
    else:
        return "?"
                
def find_close_paren(string, index, open='(', closed=')'):
    balance = 0
    for i in range(index, len(string)):
        if string[i] == open:
            balance += 1
        elif string[i] == closed:
            balance -= 1
        if balance == 0:
            return i
    raise ValueError("Unbalanced parenthesis in "+string)
    
def log(message, also_print=True):
    # todo - actual logging
    if also_print:
        print str(message)
        
def take_screenshot(screen):
    log("Taking screenshot...")
    create_dir_if_doesnt_exist("screenshots")
    existing_files = [file for file in os.listdir("screenshots") if str(file).endswith(".png")]
    num_files = len(existing_files)
    i = num_files
    while "screenshot_"+str(i)+".png" in existing_files:
        i += 1
    filename = "screenshots/screenshot_"+str(i)+".png"
    log("Saving "+filename+"...")
    pygame.image.save(screen, filename)
    
def create_dir_if_doesnt_exist(directory):
    if not os.path.exists(directory):
        log(directory + " doesn't exist. Creating...")
        os.makedirs(directory)
                
if __name__ == "__main__":
    json_datas = {
        "info": {
            "name":"Test Level",
            "version":"1.1"
        },
        "blocks": [
            {"type":"normal", "x":0, "y":128, "width":128, "height":288},
            {"type":"normal", "x":128, "y":192, "width":352, "height":224},
            {"type":"normal", "x":704, "y":288, "width":160, "height":192},
            {"type":"bad", "x":288, "y":160, "width":32, "height":32},
            {"type":"finish", "x":288, "y":100, "width":16, "height":16}
        ],
        "themes":{
            "default":"ice"
        },
        "spawns":[
            {"type":"spawn", "x":0, "y":0, "actor":"player"},
            {"type":"spawn", "x":200, "y": -100, "actor": {"type":"smart", "x":938, "y":32, "width":24, "height":32}}
        ],
        "just_an_int":45,
        "lists_within_lists": [
            ["a", "b", "c"],
            ["a", ["b", "c"]]
        ]
    }
    
    print level_json_to_string(json_datas)
    
def extend_to(text, length):
    text = str(text)
    if len(text) < length:
        return text + " "*(length - len(text))
    else:
        return text
        
def filter_and_save_discarded(iterable, test):
    res = []
    discard = []
    for value in iterable:
        if test(value):
            res.append(value)
        else:
            discard.append(value)
    return res, discard



   
    
