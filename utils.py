from __future__ import print_function
import sys

class Color:
    """
    Use for indices in lists for Board and for Q tables
    """
    EMPTY, BLACK, WHITE, BORDER = range(4)
    Empty, Black, White, Border = range(4)

def xy_to_z(x,y,n):
    """
    Transform coordinates (x,y) in 2D to a single dimension in row-major order
    :param x:
    :param y:
    :return:
    """
    return x*n+y


def z_to_xy(z,n):
    x=int(z/n)
    y=z%n
    return (x,y)


def letter2int(c):
    if c is None:
        return Color.EMPTY
    elif c == 'b':
        return Color.BLACK
    elif c == 'w':
        return Color.WHITE

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
