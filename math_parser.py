import math


EMDAS = {
    '+': lambda a, b: lambda s: a(s) + b(s),
    '-': lambda a, b: lambda s: a(s) - b(s),
    '*': lambda a, b: lambda s: a(s) * b(s),
    '/': lambda a, b: lambda s: a(s) / b(s),
    '**': lambda a, b: lambda s: a(s) ** b(s),
}


SCOPE = {
    # Function tuples are specified as:
    #   (lambda, minimum arguments, maximum arguments)
    # Where None signifies no maximum or minimum.
    'sin': (lambda args: math.sin(args[0]), 1, 1),
    'cos': (lambda args: math.cos(args[0]), 1, 1),
    'max': (lambda args: max(args), 1, None),
    'min': (lambda args: min(args), 1, None),
    'abs': (lambda args: abs(args[0]), 1, 1),
    'pi': math.pi,
}


class MalformedException(Exception):
    pass


def badfix(string):
    string = string.replace(',', ' , ')
    for op in EMDAS:
        string = string.replace(op, ' ' + op + ' ')
    return string


def comma_split(tree):
    if not tree:
        return tree
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


def parse_tree(string):
    string = badfix(string)
    split = [[y.strip() for y in x.split(')')] for x in string.split('(')]
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
    # Handles scalar constants and resolves names at runtime
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

    # Handles function calls
    if len(tree) == 2:
        fname = expression(tree[0])
        args = [expression(arg) for arg in comma_split(tree[1])]

        def func(scope):
            f, min_args, max_args = fname(scope)

            min_args = min_args and len(args) < min_args
            max_args = max_args and len(args) > max_args

            if min_args or max_args:
                raise MalformedException(
                    'Wrong number of arguments in function call',
                    tree
                )

            return f([arg(scope) for arg in args])
        return func

    # No pattern was matched, so the rest of the tree can't be parsed
    raise MalformedException('Unable to parse expression', tree)


def pythonify(string):
    """Returns a Python function that evaluates the given expression string.
    Supports multivariate expressions such as "x + y + z". Values for each
    variable are specified via keyword arguments to the returned function, for
    the above example `f(x=0, y=1, z=2)` would return `3`.

    Malformed expressions, those with unbalanced parenthesis or incorrect input
    for a function or operation, will raise a new MalformedException.

    Supported operations: +, -, *, /, **

    Supported functions: sin, cos, max, min, abs

    Built-in constants: pi

    >>> pythonify('x + y + z')(x=0, y=1, z=2)
    3
    >>> pythonify('sin(pi*x)')(x=0.5)
    1.0
    >>> pythonify('max(x, y, z)')(x=0, y=2, z=1)
    2
    """
    expr = expression(parse_tree(string))

    def evaluate(**kwargs):
        scope = dict(SCOPE)
        scope.update(kwargs)
        return expr(scope)
    return evaluate
