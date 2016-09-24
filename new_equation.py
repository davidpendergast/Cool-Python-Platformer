from functools import reduce
import math


_OP_MAP = {
    '+':    lambda a: lambda t: sum([x(t) for x in a]),
    '-':    lambda a: lambda t: a[0](t) - a[1](t),
    '*':    lambda a: lambda t: reduce(lambda a, b: a * b, [x(t) for x in a]),
    '/':    lambda a: lambda t: a[0](t) / a[1](t),
    '**':   lambda a: lambda t: a[0](t) **a[1](t),
    '%':    lambda a: lambda t: a[0](t) % a[1](t),
    'max':  lambda a: lambda t: max([x(t) for x in a]),
    'min':  lambda a: lambda t: min([x(t) for x in a]),
    'abs':  lambda a: lambda t: abs(a[0](t)),
    'cos':  lambda a: lambda t: math.cos(a[0](t)),
    'sin':  lambda a: lambda t: math.sin(a[0](t)),
}


def _value(x):
    if x == 'pi':
        return lambda t: math.pi
    try:
        f = float(x)
        return lambda t: f
    except:
        return lambda t: t


def tokenize(statement):
    statement = statement.replace('(', ' ( ').replace(')', ' ) ')
    tokens =[x for x in statement.split(' ') if len(x) > 0]
    tokens.reverse()
    return tokens


def tokes_to_trees(tokens):
    tree = []
    while len(tokens) > 0:
        t = tokens.pop()
        if t == '(':
            tree.append(tokes_to_trees(tokens))
        elif t == ')':
            return tree
        else:
            tree.append(t)
    return tree


def parse(tree):
    cdr = [parse(x) if isinstance(x, list) else _value(x) for x in tree[1:]]
    return _OP_MAP[tree[0]](cdr) if tree[0] in _OP_MAP else _value(tree[0])


def pythonify(statement):
    tree = tokes_to_trees(tokenize(statement))
    if len(tree) == 1 and isinstance(tree[0], list):
        tree = tree[0]
    return parse(tree)
