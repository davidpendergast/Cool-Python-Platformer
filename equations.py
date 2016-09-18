import math

class Expression:
    def __init__(self):
        self.symbol = "?"
        
    @staticmethod
    def get_expression(expression_string):
        list = Expression.to_list(expression_string)
        return Expression.list_to_expression(list)
    
    @staticmethod
    def list_to_expression(var):
        if type(var) == type([]):
            sym = var[0]
            elements = var[1:]
            args = []
            for element in elements:
                exp = Expression.list_to_expression(element)
                args.insert(len(args), exp)
            
            return ExpressionFactory.get_expression(sym, args)
            
        elif Number.matches(var):
            return Number(str(var))
        elif Variable.matches(var):
            return Variable()
        else:
            raise ValueError("Value not parseable: "+str(var))
    @staticmethod
    def get_paren_close_index(string, start_index):
        balance = 0;
        for index in range(start_index, len(string)):
            if string[index] == '(':
                balance += 1
            elif string[index] == ')':
                balance -= 1
            if balance == 0:
                return index
        return None
    
    @staticmethod
    def to_list(expr_string):
        if expr_string[0] == '(' and expr_string[len(expr_string)-1] == ')':
            string = expr_string[1:len(expr_string)-1]
            list = []
            while len(string) > 0:
                if string[0] == ' ':
                    string = string[1:]
                elif string[0] == '(':
                    outer_index = Expression.get_paren_close_index(string, 0)
                    list.insert(len(list), Expression.to_list(string[0:outer_index+1]))
                    string = string[outer_index+1:]
                else:
                    end = string.find(' ')
                    if end < 0:
                        end = len(string)
                    list.insert(len(list), string[0:end])
                    string = string[end+1:]         
            return list   
        else:
            return expr_string
    
    @staticmethod
    def matches(string):
        return len(string) > 2 and string[0] is '(' and string[len(string)-1] is ')'
    
    def value(self, t):
        return 0
    
class Combiner(Expression):
    def __init__(self, list):
        if len(list) != 2:
            raise ValueError("Incorrect number of arguments for "+type(self))
        self.left = list[0]
        self.right = list[1]
    def __str__(self):
        return "".join(["(", self.symbol, " ", str(self.left), " ", str(self.right), ")"])
        
class Transformer(Expression):
    def __init__(self, list):
        if len(list) != 1:
            raise ValueError("Incorrect number of arguments for "+type(self))
        self.inner = list[0]
        
    def __str__(self):
        return "".join(["(", self.symbol, " ", str(self.inner), ")"])

class Sum(Combiner):
    def value(self, t): 
        return self.left.value(t) + self.right.value(t)
          
class Difference(Combiner):
    @staticmethod
    def value(self, t):
        return self.left.value(t) - self.right.value(t)
        
class Product(Combiner):
    def value(self, t):
        return self.left.value(t) * self.right.value(t)

class Quotient(Combiner):
    def value(self, t):
        return self.left.value(t) / self.right.value(t)
   
class Exponent(Combiner):
    def value(self, t):
        return self.left.value(t) ** self.right.value(t)

class Modulo(Combiner):
    def value(self, t):
        return self.left.value(t) % self.right.value(t)
        
class Max(Combiner):
    def value(self, t):
        return max(self.left.value(t), self.right.value(t))
        
class Min(Combiner):
    def value(self, t):
        return min(self.left.value(t), self.right.value(t))
       
class Abs(Transformer):
    def value(self, t):
        return abs(self.inner.value(t))

class Cos(Transformer):
    def value(self, t):
        return math.cos(self.inner.value(t))

class Sin(Transformer):
    def value(self, t):
        return math.sin(self.inner.value(t))
        
class Number(Expression):
    def __init__(self, string):
        if string == "pi":
            self.num = math.pi
        else:
            self.num = float(string)
    
    @staticmethod
    def matches(string):
        if string == "pi":
            return True
        try:
            float(string)
            return True
        except (TypeError, ValueError) as e:
            return False
            
    def value(self, t): 
        return self.num
        
    def __str__(self):
        return str(self.num)

class Variable(Expression):
    def __init__(self):
        pass
            
    @staticmethod
    def matches(string):
        return string is 't'
        
    def value(self, t):
        return t
        
    def __str__(self):
        return "t"

class ExpressionFactory:    
    @staticmethod
    def get_expression(sym, args):
        expr = None
        if sym == '+': expr = Sum(args)
        elif sym == '-': expr = Difference(args)
        elif sym == '*': expr = Product(args)
        elif sym == '/': expr = Quotient(args)
        elif sym == '**': expr = Exponent(args)
        elif sym == '%': expr = Modulo(args)
        elif sym == 'max': expr = Max(args)
        elif sym == 'min': expr = Min(args)
        elif sym == 'abs': expr = Abs(args)
        elif sym == 'cos': expr = Cos(args)
        elif sym == 'sin': expr = Sin(args)
        
        if expr != None:
            expr.symbol = sym
        
        return expr
        