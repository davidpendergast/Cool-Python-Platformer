import math


EMDAS = {
    '+' : lambda a, b: lambda s: a(s) + b(s),
    '-' : lambda a, b: lambda s: a(s) - b(s),
    '*' : lambda a, b: lambda s: a(s) * b(s),
    '/' : lambda a, b: lambda s: a(s) / b(s),
    '**': lambda a, b: lambda s: a(s) ** b(s),
}


SCOPE = {
    'sin': lambda args: math.sin(args[0]),
    'cos': lambda args: math.cos(args[0]),
    'max': lambda args: max(args),
    'min': lambda args: min(args),
    'abs': lambda args: abs(args[0]),
    'pi' : math.pi,
}


class MalformedException(Exception):
    pass


def badfix(string):
    string = string.replace(',', ' , ')
    for op in EMDAS:
        string = string.replace(op, ' ' + op + ' ')
    return string


def comma_split(tree):
    if ',' in tree:
        i = tree.index(',')
        l = tree[:i]
        r = tree[i + 1:]
        return [l] + comma_split(r)
    return [tree]


def descend(tree, depth):
    if depth == 0:
        return tree
    if not isinstance(tree[-1], list):
        tree.append([])
    return descend(tree[-1], depth - 1)


def paren(string):
    split = [[y.strip() for y in x.split(')')] for x in badfix(string).split('(')]
    tree = [x for x in split[0][0].split(' ') if x]
    depth = 0
    for s in split[1:]:
        node = descend(tree, depth)
        node.append([x for x in s[0].split(' ') if x])
        depth += 1
        for n in s[1:]:
            depth -= 1
            if len(n) > 0:
                node = descend(tree, depth)
                node += [x for x in n.split(' ') if x]
    if depth != 0:
        raise MalformedException('Unmatched parenthesis in expression', string)
    return tree


def expression(tree):
    if not isinstance(tree, list):
        try:
            f = float(tree)
            return lambda s: f
        except:
            n = tree
            return lambda s: s[n]
    if len(tree) == 1:
        return expression(tree[0])
    for op in EMDAS.keys():
        if op in tree:
            i = tree.index(op)
            l = tree[:i]
            r = tree[i+1:]

            if l == [] and op == '-':
                r = expression(r)
                return lambda s: -1 * r(s)

            return EMDAS[op](
                expression(l),
                expression(r),
            )
    if len(tree) == 2:
        f = expression(tree[0])
        args = [expression(arg) for arg in comma_split(tree[1])]
        return lambda s: f(s)([arg(s) for arg in args])
    raise MalformedException('Unable to parse expression', tree)
    return lambda s: None


def pythonify(string):
    expr = expression(paren(string))
    def evaluate(**kwargs):
        scope = dict(SCOPE)
        scope.update(kwargs)
        return expr(scope)
    return evaluate
