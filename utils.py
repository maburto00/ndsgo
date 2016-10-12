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
    #Empty, Black, White, Border = range(4)


def xy2z(x, y, N):
    """
    Transform coordinates (x,y) in 2D to a single dimension in row-major order
    :param x:
    :param y:
    :return:
    """
    return x  + (y-1) * (N+1)


def z2xy(z, N):
    x = int(z / N)
    y = z % N
    return (x, y)


def cd2xy(s, N):
    letter = s[0].upper()
    number = s[1:]
    x = x_str.index(letter)
    y = N - int(number)
    return (x, y)


def xy2cd(x, y, N):
    letter = x_str[x]
    number = str(N - y)
    return letter + number

def cd2z(s,N):
    letter = s[0].upper()
    number = s[1:]
    x = x_str.index(letter)
    y = N - int(number)
    return x*N + y


def letter2int(c):
    if c is None:
        return Color.EMPTY
    elif c == 'b':
        return Color.BLACK
    elif c == 'w':
        return Color.WHITE



def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
