import math

import math_parser

class Path:
    def __init__(self, x_path_string, y_path_string):
        self.t = 0;
        self.path_strings = (x_path_string, y_path_string) # used for serialization
        self.x_fun = math_parser.pythonify(x_path_string)
        self.y_fun = math_parser.pythonify(y_path_string)
        
    def get_xy(self, time=None):
        if time == None:
            time = self.t
        x = self.x_fun(t=time)
        y = self.y_fun(t=time)
        
        # rounding
        x = int(x + 0.5) 
        y = int(y + 0.5)
        return (x,y)
        
    def step(self, dt):
        self.t += dt
            
    def to_json(self):
        return {
            "type":"path",
            "x_path":self.path_strings[0],
            "y_path":self.path_strings[1]
        }
    
    def is_funct_path(self): return True
    def is_point_path(self): return False
        
        
class PointPath(Path):  
    def __init__(self, x_points, y_points, speed=3, offset=0):
        self.x_points = x_points
        self.y_points = y_points
        self.speed = speed
        self.offset = offset
        
        if len(self.x_points) < 2 or len(self.y_points) < 2 or len(self.x_points) != len(self.y_points):
            raise ValueError("Path given arrays of invalid lengths: x_points="+str(len(self.x_points))+", y_points="+str(len(self.y_points)))
        
        start = offset % len(self.x_points)
        next = (offset + 1) % len(self.x_points)
        Path.__init__(self, 
                self.get_spline_string(self.x_points[start], self.x_points[next]), 
                self.get_spline_string(self.y_points[start], self.y_points[next]))
        self.dest_index = next
        self.at_end_of_spline = False
        
    def get_xy(self, time=None):
        if time != None:
            raise NotImplementedError("can't supply time arg for PointPath")
        if self.at_end_of_spline:
            return (self.x_points[self.dest_index], self.y_points[self.dest_index])
        else:
            return Path.get_xy(self)
            
    def step(self, dt):
        if self.at_end_of_spline:
            #time to move to next spline
            self.t = 0
            self.dest_index = (self.dest_index + 1) % len(self.x_points)
            
            self.x_fun = math_parser.pythonify(self.get_spline_string(
                    self.x_points[self.dest_index-1], 
                    self.x_points[self.dest_index]))
            self.y_fun = math_parser.pythonify(self.get_spline_string(
                    self.y_points[self.dest_index-1], 
                    self.y_points[self.dest_index]))
                    
            self.at_end_of_spline = False
      
        self.t += dt
        inner = self.speed * 0.01 * self.t
        if inner > math.pi:
            self.at_end_of_spline = True
        
    def get_spline_string(self, x1, x2):
        d = (x2 - x1)
        x1 = str(x1)
        if d == 0:
            return x1
        x2 = str(x2)
        d = str(d)
        speed = str(self.speed)
        
        return x1 + " + ("+d+"/2) * (1 - cos(t*" + speed + "*0.01))"
        
    def to_json(self):
        return {
            "type":"pointpath",
            "x_points":self.x_points,
            "y_points":self.y_points,
            "speed":self.speed,
            "offset":self.offset
        }
    
    def is_funct_path(self): return False
    def is_point_path(self): return True
        

def from_json(json_data):
    if json_data["type"] == "pointpath":
        return PointPath(
                json_data["x_points"],
                json_data["y_points"],
                json_data["speed"],
                0 if not "offset" in json_data else json_data["offset"]
        )
    elif json_data["type"] == "path":
        return Path(json_data["x_path"], json_data["y_path"])
        
    
        