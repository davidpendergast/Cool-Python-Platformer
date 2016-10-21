import time
import sets
import utilities


_START_TIMES = {}
_TOTAL_TIMES = {}
_GROUPS = {}
_PARENTS = {}       # mapping from event to their groups

def start(event_name, group_name=None):
    _START_TIMES[event_name] = _current_time_millis()
    _add_to_group(group_name, event_name)
    if event_name not in _TOTAL_TIMES:
        _TOTAL_TIMES[event_name] = 0
        
def _add_to_group(group_name, child_name):
    _PARENTS[child_name] = group_name
    if group_name is not None:
        if group_name not in _GROUPS:
            _GROUPS[group_name] = sets.Set()
        _GROUPS[group_name].add(child_name)
       
def group_time(group_name):
    return sum([event_time(event) for event in _GROUPS[group_name]])

def end(event_name):
    elapsed_time = _current_time_millis() - _START_TIMES[event_name]
    _TOTAL_TIMES[event_name] += elapsed_time
    _START_TIMES[event_name] = -1
    
def all_events():
    return _TOTAL_TIMES.keys()
    
def all_groups():
    return _GROUPS.keys()
    
def event_time(event_name):
    if event_name in _TOTAL_TIMES:
        return _TOTAL_TIMES[event_name]
    else:
        return -1
        
def clear():
    _TOTAL_TIMES.clear()
    _START_TIMES.clear()
    _PARENTS.clear()
    _GROUPS.clear()
    
def has_events():
    return len(_TOTAL_TIMES) > 0
         
def _current_time_millis():
    return time.time() * 1000
    
def total_time():
    return sum([group_time(group) for group in _GROUPS.keys()])
    
def get_text_summary():
    lines = []
    total = total_time()
    lines.append("total time: "+str(total))
    for group in _GROUPS.keys():
        group_total_time = group_time(group)
        lines.append(group + ": " + _percent_str(group_total_time, total) +"\t" + str(group_total_time))
        for child in _GROUPS[group]:
            child_time = event_time(child)
            lines.append("\t" + utilities.extend_to(child + ": ", 30)  + _percent_str(child_time, group_total_time) + "\t" + str(child_time))
            
    return "\n".join(lines)
        
def _percent_str(numer, denom):
    return str(round(1000*numer/denom)/10) + "%"

    
