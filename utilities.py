class Utils:
    @staticmethod
    def format_time(time):
        "75 -> '1:15'"
        if time == None:
            return None
        if time % 60 < 10:
            millis = "0" + str(time % 60)
        else:
            millis = str(time % 60)
        return str(time // 60) + ":" + millis
    @staticmethod
    def unformat_time(time_str):
        "'1:15' -> 75"
        if time_str == None:
            return None
        split = time_str.split(":")
        if len(split) == 2:
            return int(split[0])*60 + int(split[1])
        else:
            raise ValueError("invalid time string to unformat: "+str(time_str))