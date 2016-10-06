import random
import re
import options
import json

def format_time(ticks):
    "75 -> '1:15'"
    if ticks == None:
        return None
    millis = int(ticks_to_millis(ticks) + 0.5)
    
    secs = str(millis // 1000)
    millis = str(millis % 1000)
    millis = pad_to_length(millis, length=3, filler='0', to_front=True)
    
    return secs + ":" + millis


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
    return (1000 * ticks) / float(options.HardSettings.fps())
    

def millis_to_ticks(millis):
    return (millis * options.HardSettings.fps()) / float(1000)
    

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


def make_json_pretty(json_string, __nuke_it=True):
    "removes newlines between elements of innermost lists."
    m = re.search('[({[]', json_string)    
    if m == None:
        if __nuke_it:
            # json_string has no inner list
            return re.sub("\s*,\s*", ", ", json_string)
    else:
        i = m.start(0)
        j = find_close_paren(json_string, i, json_string[i], paren_dict[json_string[i]])
        substring = make_json_pretty(json_string[i+1:j], True)
        
        return json_string[:i+1] + substring + make_json_pretty(json_string[j:], False)
                
    return json_string
    
def level_json_to_string(json_data, indent_spaces=4, sort_the_keys=True):
    result = "{"
    
    keys =  sorted(json_data.keys()) if sort_the_keys else json_data.keys()
    for top_level_key in keys:
        value = json_data[top_level_key]
        result += "\n"+(" "*indent_spaces)+"\""+top_level_key+"\": "
        
        if isinstance(value, list):
            result += "["
            value_list = sorted(value) if sort_the_keys else value
            for element in value_list:
                elem_str = json.dumps(element, sort_keys=sort_the_keys)
                result += "\n"+(" "*2*indent_spaces)+elem_str+","
            if result[-1] == ",":
                result = result[0:len(result)-1]
            if len(value) > 0:
                result += "\n"+(" "*indent_spaces)
            result += "],"
        elif isinstance(value, dict):
            result += "{"
            value_keys = sorted(value.keys()) if sort_the_keys else value.keys()
            for key in value_keys:
                result += "\n"+(" "*2*indent_spaces)+"\""+key+"\":"+json.dumps(value[key], sort_keys=sort_the_keys)+","
            if result[-1] == ",":
                result = result[0:len(result)-1] 
            if len(value) > 0:
                result += "\n"+(" "*indent_spaces)
            result += "},"
        else:
            result += json.dumps(value, sort_keys=sort_the_keys)+","
    if result[-1] == ",":
        result = result[0:len(result)-1]
    if result != "{":
        result += "\n"
    
    return result + "}"
                
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


   
    
