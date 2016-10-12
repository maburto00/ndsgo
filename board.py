from utils import Color, xy2z,cd2p,rc2p

# TODO: test for scoring 2x2 board in these possitions (compare with glGo for example
# TODO: ..    X.    O.    O.
# TODO: ..    .X    .O    OO  etc...

NS = 19 + 1
WE = 1
letter_coord= 'ABCDEFGHJKLMNOPQRST'
color_string='.XOY'

class KoError(Exception):
    pass


class SuicideError(Exception):
    pass


class NotEmptyError(Exception):
    pass


class Board:
    def __init__(self, N):
        self.N = N

        # update NS
        NS = N + 1

        self.board = [Color.BORDER for _ in range(N + 1)] + \
                     N * ([Color.BORDER] + [Color.EMPTY for _ in range(N)]) + \
                     [Color.BORDER for _ in range(N + 1)]
        self.ko = None
        # captured stones
        self.CS = {'b': 0, 'w': 0}
        self.history = []
        self.last_move = None

    def _get_group_liberties(self, temp_board, p, c):
        target_color = self.board[p]

        q = [p]
        liberties = []
        while q:
            a = q.pop()
            temp_board[a] = c
            for n in (p - NS, p + NS, p - WE, p + WE):
                if temp_board[n] == target_color:
                    q.append(n)
                if temp_board[n] == Color.EMPTY:
                    liberties.append(n)
        return liberties

    def _surrounded(self, p):
        color = self.board[p]

        # make copy of board and flood fill
        temp_board = self.board[:]

    def play(self, color, p):
        # TODO: disallow suicide
        # TODO: capture
        # TODO: determine ko

        if p == self.ko:
            raise KoError

        self.board[p] = color

        # # check for each neighbor
        # for neighbor in (p - NS, p + NS, p - WE, p + WE):
        #     #explore if it was captured
        #     group,liberties = self._get_group_liberties(self.board[:],neighbor,color)
        #     if not liberties:
        #         for e in group:
        #             self.board[e]=Color.EMPTY
        #
        #
        #     temp_board=self._floodfill(neighbor)

        # check for suicide...

        #before the end store last move
        self.last_move = p

    def __str__(self):
        """
            'X' for black, 'O' for white and '.' for empty space
        """
        result = '\n\n'

        for row in range(1,self.N+1):
            result += '{:2} '.format(self.N+1-row)
            for col in range(1,self.N+1):
                p = rc2p(row, col, self.N)
                color_str = color_string[self.board[p]]
                if p == self.last_move:
                    result = result[:-1]
                    result += '('+color_str+')'
                else:
                    result += color_str+' '
            result +='\n'
        result += '   ' + ''.join('{} '.format(c) for c in letter_coord[:self.N])

        return result

    #     def is_legal(self,row,col,color):
    #         if self.board[row][col] is None:
    #             return True
    #         #TODO: implement ko
    #         # if self.ko is not None:
    #         #     if (self.ko==(row,col)):
    #         #         return False
    #         #if self.is_suicide(row,col)
    #
    #     # def get_group(self,pos):
    #     #     """
    #     #     return list of positions adjacent to pos
    #     #     :param pos:
    #     #     :return:
    #     #     """
    #     #     group=[]
    #     #
    #     #     to_explore=set()
    #     #     to_explore.add(pos)
    #     #     while True:
    #     #         current_pos=to_explore.pop()
    #     #         if current_pos not in group: #maybe this validation is unnecessary
    #     #             group.append(pos)
    #     #         #explore up,down,left and right:
    #     #         if UP(pos) not in group:
    #
    #     # def get_liberties(self,pos):
    #     #     (row,col)=pos
    #     #     color=self.board[row][col]
    #     #
    #     # def is_suicide(self,row,col):
    #     #     pos=(row,col)
    #     #     if (UP(pos) is None or DOWN(pos) is None or
    #     #         LEFT(pos) is None or RIGHT(pos) is None):
    #     #         return False
    #     #     else:
    #     #         lib=self.get_liberties(UP(pos))
    #
    #     def get_groups(self):
    #         #hacer busqueda por profundidad
    #         to_explore=set()
    #         to_explore.add(point)
    #         already_in_group=[]
    #         groups=[] #list of Groups
    #
    #         for (row,col) in self.board_points:
    #             if (row,col) in already_in_group:
    #                 continue
    #             #initiate group
    #             group=[(row,col)]
    #
    #
    #     def get_surrounded(self,x,y):
    #         """
    #         get surrounded groups
    #         :param x:
    #         :param y:
    #         :return:
    #         """
    #         pos=(x,y)
    #         check_points=[pos,UP(),DOWN(pos),LEFT(pos),RIGHT(pos)]
    #         for p in check_points:
    #             group=get_group(p)
    #
    #
    #     def play(self, x, y, color):
    #         # TODO: manage captures
    #         # DONE: illegal move (NotEmptyError)
    #         # TODO: illegal move (suicide)
    #         # TODO: manage illega molve (simple ko)
    #         if self.board[x][y] is not None:
    #             raise NotEmptyError
    #         self.board[x][y] = color
    #         surrounded=self.get_surrounded(x,y)
    #         if surrounded:
    #             #if len(surrounded)==1: #only one group is surrounded
    #             #   pass
    #             #    if len(surrounded[0])==1: #the group has only one stone (it could be a ko)
    #             #else:
    #             for group in surrounded: #capture stones
    #                 for pos in group:
    #                     (row,col)=pos
    #                     self.board[row][col]=None
    #         else:
    #             #undo move
    #             self.board[x][y] = None
    #             raise SuicideError
    #
    #
    #
    #         #if surrounded=[] then it is an illegal move
    #
    #     def reset(self):
    #         self.board = [[None for _ in range(n)] for _ in range(n)]
    #         self.ko = None
    #
    #     def get_available_pos(self):
    #         # TODO: manage the illegal moves (not empty)
    #         # TODO: manage the illegal moves (suicide)
    #         # TODO: manage the illegal moves (ko)
    #         """ return valid moves....
    #         :return:
    #         """
    #         list_pos = []
    #         for i in range(self.n):
    #             for j in range(self.n):
    #                 if self.board[i][j] is None and self.ko != (i, j):
    #                     list_pos.append((i, j))
    #         return list_pos
    #
    #

    # def test1():
    #     print('Test 1----------')
    #     board = Board(5)
    #     board.play(1,2,'b')
    #     board.play(2, 3, 'b')
    #     board.play(3, 2, 'b')
    #     board.play(2, 2, 'w')
    #     print(board)
    #
    # # used to test
def test_init():
    board = Board(3)
    print(board.board)

def test_play():
    print('Test for board class')
    board = Board(5)
    board.play(Color.BLACK, cd2p('A1', 5))
    print(board)
    board.play(Color.WHITE, cd2p('E5', 5))
    print(board)


if __name__ == '__main__':
    #main()
    #test_init()
    test_play()
