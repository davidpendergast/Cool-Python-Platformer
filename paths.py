import math

import equations

class Path:
    def __init__(self, x_expression, y_expression, integral=True):
        self.t = 0;
        self.x_fun = x_expression
        self.y_fun = y_expression
        self.integral=integral
        
    def get_xy(self):
        x = self.x_fun(self.t)
        y = self.y_fun(self.t)
        if self.integral:
            x = int(x + 0.5) # rounding
            y = int(y + 0.5)
        return (x,y)
        
    def step(self, dt):
        self.t += dt
    
    def add_to_json(self, json_dict):
        json_dict["x_path"] = str(self.x_expression)
        json_dict["y_path"] = str(self.y_expression)
        
        
class PointPath(Path):  
    def __init__(self, x_points, y_points, speed=3):
        self.x_points = x_points
        self.y_points = y_points
        self.speed = speed
        if len(self.x_points) < 2 or len(self.y_points) < 2 or len(self.x_points) != len(self.y_points):
            raise ValueError("Path given arrays of invalid lengths: x_points="+str(len(self.x_points))+", y_points="+str(len(self.y_points)))
        self.dest_index = 1
        
        Path.__init__(self, self.get_spline_funct(self.x_points[0],self.x_points[1]), self.get_spline_funct(self.y_points[0],self.y_points[1]))
        
        self.at_end_of_spline = False
        
    def get_xy(self):
        if self.at_end_of_spline:
            return (self.x_points[self.dest_index], self.y_points[self.dest_index])
        else:
            return Path.get_xy(self)
            
    def step(self, dt):
        if self.at_end_of_spline:
            #time to move to next spline
            self.t = 0
            self.dest_index = (self.dest_index + 1) % len(self.x_points)
            
            self.x_fun = self.get_spline_funct(self.x_points[self.dest_index-1], self.x_points[self.dest_index])
            self.y_fun = self.get_spline_funct(self.y_points[self.dest_index-1], self.y_points[self.dest_index])
            self.at_end_of_spline = False
      
        self.t += dt
        inner = self.speed * 0.01 * self.t
        if inner > math.pi:
            self.at_end_of_spline = True
        
    def get_spline_funct(self, x1, x2):
        d = (x2 - x1)
        if d == 0:
            return equations.pythonify(str(x1))
        spline_string = "(+ "+str(x1)+" (* (/ "+str(d)+" 2) (- 1 (cos (* "+str(self.speed)+" 0.01 t)))))"
        return equations.pythonify(spline_string)
        
    def add_to_json(self, json_dict):
        json_dict["x_points"] = self.x_points
        json_dict["y_points"] = self.y_points
        