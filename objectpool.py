import sets

class ObjectPool:
    def __init__(self, generator, cleaner=lambda x: x, initial_size=1):
        self._objects = []
        self._generator = generator
        self._cleaner = cleaner
        for i in range(0, initial_size):
            self._objects.append(generator())
    
    def get(self):
        if len(self._objects) > 0:
            return self._objects.pop()
        else:
            return self._generator()
    
    def put_back(self, obj):
        self._cleaner(obj)
        self._objects.append(obj)
        
SET_POOL = ObjectPool(lambda: sets.Set(), lambda x: x.clear(), 0)
DICT_POOL = ObjectPool(lambda: {}, lambda x: x.clear(), 0)
        