from __future__ import print_function
import sys

# TODO: use new coordinate starting that go from 1 to N instead of 0 to N-1
# TODO: maybe use only one dimensional coordinates internally to simplify code (not use x,y anymore but only z)
# TODO: delete unused functions

letter_coord = 'ABCDEFGHJKLMNOPQRST'

class Color:
    """
    Use for indices in lists for Board (not for Q tables)
    """
    EMPTY, BLACK, WHITE, BORDER, FILL = range(5)
    # Empty, Black, White, Border = range(4)


def a2p(a, N):
    """
    action to position.

    action goes from 0 to N*N, p goes from 0 to (N+1)*(N+2)-1
    :param a:
    :param N:
    :return:
    """
    return N + 2 + (a % N) + (a // N) * (N + 1)

def p2a(p,N):
    return p-N-2-(p-N-2)//(N+1)


def rc2p(row, col, N):
    """
    row-col to (board) position

    row and column go from 1 to N
    Test OK
    :param row:
    :param col:
    :param N:
    :return:
    """

    # print('row:{} col:{}'.format(row,col))
    return row * (N + 1) + col


def xy2z(x, y, N):
    """
    Transform coordinates (x,y) in 2D to a single dimension in row-major order
    :param x:
    :param y:
    :return:
    """
    return x + (y - 1) * (N + 1)


def a2rc(a, N):
    """

    Test OK
    :param a:
    :param N:
    :return:
    """
    r = int(a / N)
    c = a % N
    return (r+1, c+1)


def cd2xy(s, N):
    letter = s[0].upper()
    number = s[1:]
    x = letter_coord.index(letter)
    y = N - int(number)
    return (x, y)


def rc2cd(r, c, N):
    """
    OK
    :param r:
    :param c:
    :param N:
    :return:
    """
    letter = letter_coord[c-1] #OK
    number = str(N - (r-1))
    return letter + number


def color2c(color):
    color = color.lower()
    if color == 'black' or color =='b':
        return Color.BLACK
    if color == 'white' or color=='w':
        return Color.WHITE


def c_cd2cp(s, N):
    """
    from 'b A1' to tuple (Color.BLACK, p)
    :param str:
    :return:
    """
    color, move = s.strip().split()
    # print('color:{} move:{}'.format(color,move))
    c = color2c(color)
    p = cd2p(move, N)
    return c, p


def cd2p(s, N):
    """
    e.g. from A2 in 2x2 board it returns 4 (the position in the array for that position)
    :param s:
    :param N:
    :return:
    """
    letter = s[0].upper()
    number = s[1:]
    col = letter_coord.index(letter) + 1
    row = (N + 1) - int(number)
    # print('row:{} col:{}'.format(row,col))
    return col + (N + 1) * row

def p2cd(p,N):
    """
    OK
    (board array) position to character-decimal coordinates (A1,B3,...)
    :param p:
    :param N:
    :return:
    """
    a=p2a(p,N) #OK
    (r,c)=a2rc(a,N) #OK
    return rc2cd(r, c, N)


def letter2int(c):
    if c is None:
        return Color.EMPTY
    elif c == 'b':
        return Color.BLACK
    elif c == 'w':
        return Color.WHITE


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
