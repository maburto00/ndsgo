

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
        return 0
    elif c == 'b':
        return 1
    elif c == 'w':
        return 2
