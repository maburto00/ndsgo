from __future__ import print_function
import sys

# TODO: use new coordinate starting that go from 1 to N instead of 0 to N-1
# TODO: maybe use only one dimensional coordinates internally to simplify code (not use x,y anymore but only z)

x_str = 'ABCDEFGHJKLMNOPQRST'


class Color:
    """
    Use for indices in lists for Board (not for Q tables)
    """
    EMPTY, BLACK, WHITE, BORDER = range(4)
    Empty, Black, White, Border = range(4)


def xy_to_z(x, y, n):
    """
    Transform coordinates (x,y) in 2D to a single dimension in row-major order
    :param x:
    :param y:
    :return:
    """
    return x * n + y


def z_to_xy(z, n):
    x = int(z / n)
    y = z % n
    return (x, y)


def cd2xy(str, n):
    letter = str[0].upper()
    number = str[1:]
    x = x_str.index(letter)
    y = n - int(number)
    return (x, y)


def xy2cd(x, y, n):
    letter = x_str[x]
    number = str(n - y)
    return letter + number


def letter2int(c):
    if c is None:
        return Color.EMPTY
    elif c == 'b':
        return Color.BLACK
    elif c == 'w':
        return Color.WHITE


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
