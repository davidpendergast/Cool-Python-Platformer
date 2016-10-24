class UiManager:
    def __init__(self):
        self._elements = []
        self._focused_element = None
    def draw(self, screen, offset=(0,0)):
        for element in self.elements():
            element.draw_self_and_children(screen, offset)
    def elements(self):
        return self._elements 
    
    
class UiElement:
    def __init__(self, x, y, width, height, manager):
        self.ui_manager = manager
        self._x = x
        self._y = y
        self._width = width 
        self._height = height 
        
        self._parent = None
        self._children = []
        
        self._click_actions = []
        
    def draw(self, screen, offset=(0,0)):
        pass
        
    def draw_self_and_children(self, screen, offset=(0,0)):
        self.draw(screen, offset)
        for child in self._children:
            child.draw_self_and_children(screen, offset)
        
    def update(self, dt):
        pass
    def x(self):
        return self._x
    def y(self):
        return self._y
    def width(self):
        return self._width
    def height(self):
        return self._height
    def is_focusable(self):
        return False
    def is_clickable(self):
        return False
    def add_click_action(self, click_lambda):
        self.click_actions.append(click_lambda)
    def do_click(self):
        if self.is_clickable(self):
            for click_action in self.click_actions:
                click_action()
    
class TextBox(UiElement):
    def __init__(self, text, color, x, y):
        pass
        
    
    
        