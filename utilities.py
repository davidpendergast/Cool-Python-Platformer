import random
import options

class Utils:
    @staticmethod
    def format_time(ticks):
        "75 -> '1:15'"
        if ticks == None:
            return None
        millis = Utils.ticks_to_millis(ticks)
        
        secs = str(millis // 1000)
        millis = str(millis % 1000)
        millis = Utils.pad_to_length(millis, length=3, filler='0', to_front=True)
        
        return secs + ":" + millis
    
    @staticmethod
    def unformat_time(time_str):
        "'1:15' -> 75"
        if time_str == None:
            return None
        split = time_str.split(":")
        if len(split) == 2:
            millis = int(split[0])*1000 + int(split[1])
            return Utils.millis_to_ticks(millis)
        else:
            raise ValueError("invalid time string to unformat: "+str(time_str))
            
    @staticmethod
    def lim(x, minimum, maximum):
        return min(max(x, minimum), maximum)
        
    @staticmethod
    def perturb_color(orig_color, max_perturb, only_greyscale):
        sign = (-1,1)
        if only_greyscale:
            val = sign[random.randint(0,1)]*random.randint(0,max_perturb)
            pert = val, val, val
        else:
            pert = (sign[random.randint(0,1)]*random.randint(0,max_perturb) for i in range(3))
            
        res = tuple([Utils.lim(orig_color[i]+pert[i], 0, 255) for i in range(3)])

        return res
        
    @staticmethod
    def ticks_to_millis(ticks):
        return int((1000 / options.HardSettings.fps())*ticks + 0.5)
        
    @staticmethod
    def millis_to_ticks(millis):
        return int(millis * options.HardSettings.fps() / 1000 + 0.5)
        
    @staticmethod
    def pad_to_length(string, length, filler, to_front=False):
        if len(string) >= length:
            return string
        else:
            pad = length - len(string)
            if to_front:
                return filler*pad + string
            else:
                return string + filler*pad
    