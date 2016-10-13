from utils import Color, xy2z, cd2p, rc2p, eprint, c_cd2cp

# from collections import deque
# TODO: method "get_simple_board()" in order to stop using many of the utils like a2p, cd2p, ...


# NS is overwriteng in __init__ to be N+1
NS = 19 + 1
WE = 1
letter_coord = 'ABCDEFGHJKLMNOPQRST'
color_string = '.XOY'


class Error:
    SUICIDE, KO, NONEMPTY, NOERROR = [-3, -2, -1, 0]


def opposite_color(c):
    if c == Color.WHITE:
        return Color.BLACK
    elif c == Color.BLACK:
        return Color.WHITE


class Board:
    def __init__(self, N):
        self.N = N

        # update NS
        global NS
        NS = N + 1

        self.board = [Color.BORDER for _ in range(N + 1)] + \
                     N * ([Color.BORDER] + [Color.EMPTY for _ in range(N)]) + \
                     [Color.BORDER for _ in range(N + 1)]
        self.ko = None
        # captured stones
        self.CS = {'b': 0, 'w': 0}
        self.history = []
        self.last_move = None

    def copy(self):
        board = Board(self.N)
        board.board=self.board[:]
        board.ko=self.ko
        board.CS=self.CS
        board.history=self.history
        board.last_move=self.last_move

        return board


    def _neighbors(self, p):
        """
        return neighbors in clockwise fashion
        :param p:
        :return:
        """
        return (p - NS, p + WE, p + NS, p - WE)

    def _surrounded(self, group):
        color = self.board[group[0]]
        for e in group:
            for nb in self._neighbors(e):
                if self.board[nb] == Color.EMPTY:
                    return False
        return True

    def _get_group(self, p):
        target_color = self.board[p]

        #if target_color != Color.WHITE and target_color != Color.BLACK:
        #    return []

        # copy board
        temp_board = self.board[:]

        # add p to queue
        # queue = deque([p])
        queue = [p]
        group = []
        while queue:
            # eprint('_get_group p:{} q:{} group:{} target_color:{}'.format(p,queue,group,target_color))
            # current exploring node
            a = queue.pop()
            # eprint('a:{} c(a):{}'.format(a,temp_board[a]))

            # skip if we have explored already
            if temp_board[a] == Color.FILL:
                continue

            temp_board[a] = Color.FILL
            group.append(a)

            for nb in self._neighbors(a):
                # eprint('nb:{}'.format(nb))
                if temp_board[nb] == target_color:
                    queue.append(nb)
        # eprint(temp_board)
        # eprint('group:{}'.format(group))
        return group

        # def _surrounded(self, p):

    #        color = self.board[p]

    # make copy of board and flood fill
    #        temp_board = self.board[:]

    def play(self, color, p):
        # TODO: capture
        # TODO: determine ko (and put None if there is no ko)
        # TODO: disallow suicide (SuicideError)
        # TODO: Use None instead of exceptions

        error = Error.NOERROR

        if p == self.ko:
            return Error.KO

        if self.board[p] != Color.EMPTY:
            return Error.NONEMPTY

        # put stone
        self.board[p] = color

        # detect if it is single stone autocapture point (for detecting ko)
        # later call again to detect suicide once the opposing color stones are captured.
        group = self._get_group(p)
        one_point_selfcapture = False
        if self._surrounded(group) and len(group) == 1:
            one_point_selfcapture = True

        o_color = opposite_color(color)
        possible_ko = []
        # check for each neighbor of oppossite color and mark for capture (if surrounded)
        for nb in self._neighbors(p):
            # eprint('play() p:{}  nb:{} NS:{} WE:{}'.format(p, nb,NS,WE))
            if self.board[nb] != o_color:
                # if self.board[nb] == color:
                continue
            # eprint('AFTER')
            group = self._get_group(nb)
            if self._surrounded(group):
                for e in group:
                    self.board[e] = Color.EMPTY
                if len(group) == 1 and one_point_selfcapture:
                    possible_ko.append(group[0])
                    # eprint(group)

        if len(possible_ko) == 1:
            self.ko = possible_ko[0]
        else:
            self.ko = None

        # check for suicide
        group = self._get_group(p)
        if self._surrounded(group):
            self.board[p] = Color.EMPTY
            # eprint('suicide')
            return Error.SUICIDE

        # #explore if it was captured
        #     group,liberties = self._get_group_liberties(self.board[:],neighbor,color)
        #     if not liberties:
        #         for e in group:
        #             self.board[e]=Color.EMPTY
        #
        #
        #     temp_board=self._floodfill(neighbor)

        # check for suicide...

        # before the end store last move
        self.last_move = p

        return Error.NOERROR

    def play_seq(self, seq, verbose=False):
        for s in seq:
            (c, p) = c_cd2cp(s, self.N)
            res = self.play(c, p)
            if verbose:
                eprint(self)
                eprint('res:{} ko:{}'.format(res, self.ko))
        return res

    def _group_reach(self, group, color):
        """point reaches color c."""

        for e in group:
            for nb in self._neighbors(e):
                if self.board[nb] == color:
                    return True
        return False

        # if self._surrounded(group):
        #    self.board[p] = Color.EMPTY
        #    # eprint('suicide')
        #    return Error.SUICIDE

    def score(self):
        """
        Score using Tromp-Taylor rules
        :return:
        """
        # TODO: add captures and komi as arguments

        # make a copy of board and color it
        scoring_board = self.board[:]
        # marked_board = self.board[:]

        points = [rc2p(r, c,self.N) for r in range(1, self.N + 1) for c in range(1, self.N + 1)]
        #eprint(points)
        #eprint(scoring_board)
        for p in points:
            if scoring_board[p] == Color.FILL:
                #eprint('s_board[p] is Color.FILL')
                #eprint(scoring_board)
                continue
                # if scoring_board[p]==Color.WHITE or scoring_board[p]==Color.BLACK:
            #                continue
            # we only care about empty points for coloring
            if scoring_board[p] == Color.EMPTY:
                group = self._get_group(p)
                reach_black = self._group_reach(group, Color.BLACK)
                reach_white = self._group_reach(group, Color.WHITE)

                if reach_black and not reach_white:
                    coloring = Color.BLACK
                elif not reach_black and reach_white:
                    coloring = Color.WHITE
                else:
                    coloring = Color.FILL

                for e in group:
                    scoring_board[e] = coloring

        # now score:
        b_points = sum([1 if scoring_board[i] == Color.BLACK else 0 for i in points])
        w_points = sum([1 if scoring_board[i] == Color.WHITE else 0 for i in points])

        return b_points - w_points

    def __str__(self):
        """
            'X' for black, 'O' for white and '.' for empty space
        """
        result = '\n'

        for row in range(1, self.N + 1):
            result += '{:2} '.format(self.N + 1 - row)
            for col in range(1, self.N + 1):
                p = rc2p(row, col, self.N)
                color_str = color_string[self.board[p]]
                if p == self.last_move:
                    result = result[:-1]
                    result += '(' + color_str + ')'
                else:
                    result += color_str + ' '
            result += '\n'
        result += '   ' + ''.join('{} '.format(c) for c in letter_coord[:self.N])

        return result



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


def test_play_seq():
    board = Board(5)
    seq = ['b B3', 'b C4', 'b C2', 'B D3',
           'W D4', 'w E3', 'w D2']
    board.play_seq(seq)
    eprint(board)


def test_init():
    board = Board(3)
    eprint(board.board)


def test_str():
    board = Board(19)
    board.play(Color.BLACK, cd2p('Q16', 19))
    eprint(board)
    board.play(Color.WHITE, cd2p('D4', 19))
    eprint(board)


def test_suicide():
    N = 5
    board = Board(N)
    eprint(board)
    seq = ['b B3', 'b C4', 'b C2', 'B D3',
           'W C3']
    board.play_seq(seq, True)


def test_ko():
    N = 5
    board = Board(N)
    eprint(board)
    setup = ['b B3', 'b C4', 'b C2', 'B D3',
             'W D4', 'w e3', 'w d2']

    res = board.play_seq(setup)
    eprint('\n\nAFTER SETUP')
    eprint(board)
    eprint('res:{} ko:{}'.format(res, board.ko))

    ko_seq = ['w c3', 'b d3', 'b b4', ' w b2', 'b d3', 'w c3']
    board.play_seq(ko_seq, True)


def test_capture():
    N = 5
    board = Board(N)
    eprint(board)
    seq = [(Color.BLACK, cd2p('B3', N)),
           (Color.BLACK, cd2p('C4', N)),
           (Color.BLACK, cd2p('C2', N)),
           (Color.WHITE, cd2p('C3', N)),
           (Color.BLACK, cd2p('D3', N))]

    for (c, p) in seq:
        board.play(c, p)
        eprint(board)


        # board.play(Color.BLACK, cd2p('A1', 5))
        # eprint(board)
        # board.play(Color.WHITE, cd2p('E5', 5))
        # eprint(board)


def test_nonempty():
    N = 5
    board = Board(N)
    eprint(board)
    seq = [(Color.BLACK, cd2p('B1', N)),
           (Color.BLACK, cd2p('B1', N))]
    for (c, p) in seq:
        res = board.play(c, p)
        eprint(board)
        eprint('res:{}'.format(res))


def test_get_group():
    N = 5
    board = Board(N)
    eprint(board)
    seq = [(Color.BLACK, cd2p('B1', N)),
           (Color.BLACK, cd2p('B2', N)),
           (Color.BLACK, cd2p('C1', N)),
           (Color.BLACK, cd2p('C2', N))]

    for (c, p) in seq:
        board.play(c, p)
        eprint(board)
    eprint('HHHHH')

    group = board._get_group(33)
    eprint('surrounded:{}'.format(board._surrounded(group)))
    eprint('group:{}'.format(group))


def test_score():
    board=Board(5)
    score = board.score()
    eprint(board)
    eprint('score:{}'.format(score))

    seq1=['B C5','B C4','B C3','B C2','B C1',
          'W D5','W D4','W D3','W D2','W D1',]
    res=board.play_seq(seq1)
    eprint(board)
    eprint('res:{} ko:{}'.format(res,board.ko))
    score=board.score()
    eprint('score:{}'.format(score))

    board = Board(5)
    seq2=['B B5','B B4','B B3','B B2','B B1',
          'W D5','W D4','W C3','W C2']
    res=board.play_seq(seq2)
    eprint(board)
    eprint('res:{} ko:{}'.format(res,board.ko))
    score=board.score()
    eprint('score:{}'.format(score))

    board.play_seq(['W C1'])
    eprint(board)
    eprint('res:{} ko:{}'.format(res, board.ko))
    score = board.score()
    eprint('score:{}'.format(score))


if __name__ == '__main__':
    # main()
    # test_init()
    # test_capture()
    # test_suicide()
    # test_play_seq()
    #test_ko()
    test_score()
    # test_nonempty()
    # test_get_group()
    # test_str()
