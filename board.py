from utils import Color, cd2p, rc2p, eprint, c_cd2cp,p2a
import utils
import struct

# NS is overwritten in __init__ to be N+1
NS = 19 + 1
WE = 1
letter_coord = 'ABCDEFGHJKLMNOPQRST'
color_string = 'XO.'

NUM_CHANNELS = 4  #used in dataset_generator

class Error:
    SUICIDE, KO, NONEMPTY, NOERROR = [-3, -2, -1, 0]



class Board:
    def __init__(self, N, komi=6.5):
        self.N = N

        global NS
        NS = N + 1

        self.board = [Color.BORDER for _ in range(N + 1)] + \
                     N * ([Color.BORDER] + [Color.EMPTY for _ in range(N)]) + \
                     [Color.BORDER for _ in range(N + 1)]
        self.ko = None

        self.captures = [0, 0]
        self.komi = komi

        self.move_history = []

    @staticmethod
    def opposite_color(c):
        if c == Color.WHITE:
            return Color.BLACK
        elif c == Color.BLACK:
            return Color.WHITE

    def copy(self):
        board = Board(self.N)
        board.board = self.board[:]
        board.ko = self.ko
        board.captures = self.captures
        board.move_history = self.move_history

        return board

    def clear_board(self):
        N = self.N
        self.board = [Color.BORDER for _ in range(N + 1)] + \
                     N * ([Color.BORDER] + [Color.EMPTY for _ in range(N)]) + \
                     [Color.BORDER for _ in range(N + 1)]
        self.captures[Color.BLACK] = 0
        self.captures[Color.WHITE] = 0
        self.move_history = []
        self.ko = None

    def undo(self):
        """
        reset history, captures and board to the value of the previous position
        :return:
        """
        temp_history = self.move_history[:-1]
        self.clear_board()
        for c, p in temp_history:
            self.play(c, p)

    def is_my_eye(self, c, p):
        result=True
        for n in self._neighbors(p):
            if self.board[n]!=c:
                result=False
        return result

    def _neighbors(self, p):
        """
        return neighbors in clockwise fashion
        :param p:
        :return:
        """
        return p - NS, p + WE, p + NS, p - WE

    def _surrounded(self, group):
        color = self.board[group[0]]
        for e in group:
            for nb in self._neighbors(e):
                if self.board[nb] == Color.EMPTY:
                    return False
        return True

    def _get_group(self, p):
        target_color = self.board[p]

        temp_board = self.board[:]

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

    @staticmethod
    def get_board_and_move_from_register_str(N, register_str, player_color):
        """
        :param register_str:
        :return: (board,a)
        """
        if player_color == Color.BLACK:
            opp_color = Color.WHITE
        else:
            opp_color = Color.BLACK


        register_array=[e for e in bytearray(register_str)]
        a=struct.unpack('<h',register_str[:2])[0]
        vector_array=register_array[2:]
        #eprint(vector_array)
        #eprint(len(vector_array))
        board=Board(N)
        i = 0
        for r in range(1, N + 1):
            for c in range(1, N + 1):
                if vector_array[i]==1:
                    board.board[utils.rc2p(r,c,N)] = player_color
                i += 1

        for r in range(1, N + 1):
            for c in range(1, N + 1):
                if vector_array[i]==1:
                    board.board[utils.rc2p(r,c,N)]=opp_color
                i += 1
        return board,a


    def create_board_register(self,player_color):
        if player_color == Color.BLACK:
            opp_color = Color.WHITE
        else:
            opp_color = Color.BLACK

        N = self.N
        player_stone = [0 for i in range(N*N)]
        opp_stone = [0 for i in range(N*N)]
        empty_stone = [0 for i in range(N*N)]
        all_ones = [1 for i in range(N*N)]

        i = 0
        #fill the feature planes
        for r in range(1, N + 1):
            for c in range(1, N + 1):
                if self.board[rc2p(r, c, N)] == player_color:
                    player_stone[i] = 1
                elif self.board[rc2p(r, c, N)] == opp_color:
                    opp_stone[i] = 1
                elif self.board[rc2p(r, c, N)] == Color.EMPTY:
                    empty_stone[i] = 1
                i += 1
        #eprint(player_stone)
        #eprint(opp_stone)
        #eprint(empty_stone)
        # append the first four features
        feature_planes = player_stone + opp_stone + empty_stone + all_ones

        return bytearray(feature_planes)


    def create_board_move_register(self, player_color, p):
        """
        from board position and next move, create training example in byte form
        # <label 1byte><board position features size*size*num_features bytes>
        :return:
        """
        # features 1,2,3: Player stone/opponent stone/empty
        # feature 4: all ones

        #here we define the number of feature layers that our input will have

        # <label 2 bytes><board position features size*size*num_features bytes>


        feature_planes_bytes=self.create_board_register(player_color)
        move_label = p2a(p, self.N)
        # Big Endian
        # register_array = [move_label/ 256, move_label % 256]+ feature_planes

        # little-endian
        register_bytes = bytearray([move_label % 256, move_label / 256]) + feature_planes_bytes
        # to acces the int formed by two bytes use:
        #       struct.unpack('>h', bytearray([0, 1]))[0]

        #register_bytes = bytearray(register_array)
        return register_bytes

    def add_black_handicap_stone(self,p):
        """
        for handicap games, doesn't update history, or manage captures, etc.
        :return:
        """
        self.board[p] = Color.BLACK

    def play(self, c, p):

        if p == self.ko:
            return Error.KO

        if self.board[p] != Color.EMPTY:
            return Error.NONEMPTY

        # put stone
        self.board[p] = c

        # detect if it is single stone autocapture point (for detecting ko)
        # later call again to detect suicide once the opposing color stones are captured.
        group = self._get_group(p)
        one_point_selfcapture = False
        if self._surrounded(group) and len(group) == 1:
            one_point_selfcapture = True

        o_color = Board.opposite_color(c)
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
                    self.captures[c] += 1
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

        # before the end store move in history
        self.move_history.append((c, p))

        return Error.NOERROR

    def play_seq(self, seq, verbose=False):
        for s in seq:
            (c, p) = c_cd2cp(s, self.N)
            res = self.play(c, p)
            if verbose:
                eprint(self)
                eprint('res:{} ko:{}'.format(res, self.ko))
                eprint('seq:{}', seq)
        return res

    def _group_reach(self, group, color):
        """point reaches color c."""

        for e in group:
            for nb in self._neighbors(e):
                if self.board[nb] == color:
                    return True
        return False

    def tromp_taylor_score(self):
        """
        Score using Tromp-Taylor rules
        :return:
        """

        # make a copy of board and color it
        scoring_board = self.board[:]

        points = [rc2p(r, c, self.N) for r in range(1, self.N + 1) for c in range(1, self.N + 1)]

        for p in points:
            if scoring_board[p] == Color.FILL:
                continue

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

    def final_score(self):
        score = self.tromp_taylor_score()
        return score - self.komi + self.captures[Color.BLACK] - self.captures[Color.WHITE]

    def __str__(self):
        """
            'X' for black, 'O' for white and '.' for empty space
        """
        result = '\n'

        result += 'Black: {} captures | White: {} captures | Komi: {}\n'.format(self.captures[Color.BLACK],
                                                                                self.captures[Color.WHITE],
                                                                                self.komi)
        for row in range(1, self.N + 1):
            result += '{:2} '.format(self.N + 1 - row)
            for col in range(1, self.N + 1):
                p = rc2p(row, col, self.N)
                color_str = color_string[self.board[p]]
                # if p is last move
                if self.move_history != [] and p == self.move_history[-1][1]:
                    result = result[:-1]
                    result += '(' + color_str + ')'
                else:
                    result += color_str + ' '
            result += '\n'
        result += '   ' + ''.join('{} '.format(c) for c in letter_coord[:self.N])

        return result


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
    # eprint('HHHHH')

    group = board._get_group(33)
    eprint('surrounded:{}'.format(board._surrounded(group)))
    eprint('group:{}'.format(group))


def test_score():
    board = Board(5)
    score = board.tromp_taylor_score()
    eprint(board)
    eprint('score:{}'.format(score))

    seq1 = ['B C5', 'B C4', 'B C3', 'B C2', 'B C1',
            'W D5', 'W D4', 'W D3', 'W D2', 'W D1', ]
    res = board.play_seq(seq1)
    eprint(board)
    eprint('res:{} ko:{}'.format(res, board.ko))
    score = board.tromp_taylor_score()
    eprint('score:{}'.format(score))

    board = Board(5)
    seq2 = ['B B5', 'B B4', 'B B3', 'B B2', 'B B1',
            'W D5', 'W D4', 'W C3', 'W C2']
    res = board.play_seq(seq2)
    eprint(board)
    eprint('res:{} ko:{}'.format(res, board.ko))
    score = board.tromp_taylor_score()
    eprint('score:{}'.format(score))

    board.play_seq(['W C1'])
    eprint(board)
    eprint('res:{} ko:{}'.format(res, board.ko))
    score = board.tromp_taylor_score()
    eprint('score:{}'.format(score))


def test_inf_play(verbose=True):
    board = Board(9)
    eprint(board)
    while True:
        eprint("Enter move (e.g: 'black A1' or '' for passing): ", end='')
        mov = raw_input()
        if mov == '':
            continue
        c, p = c_cd2cp(mov, board.N)
        res = board.play(c, p)
        if verbose:
            eprint(board)
            eprint('res:{} ko:{}'.format(res, board.ko))


def test_eyes():
    board = Board(19)
    eprint(board)
    # SETUP
    seq1 = ['B C4', 'B D5', 'B D3', 'B E4',
            'W B4', 'W C3', 'W C5', 'W D2', 'W D6', 'W E3', 'W E5', 'W F4']
    seq2 = ['B C11', 'B D11', 'B E11', 'B F11', 'B G11', 'B C10', 'B E10', 'B G10', 'B C9', 'B D9', 'B E9', 'B F9',
            'B G9',
            'W C12', 'W D12', 'W E12', 'W F12', 'W G12', 'W B11', 'W H11', 'W B10', 'W H10', 'W B9', 'W H9', 'W C8',
            'W D8', 'W E8', 'W F8', 'W G8']
    seq3 = ['B C17', 'B D17', 'B E17', 'B C16', 'B E16', 'B C15', 'B D15', 'B E15',
            'W C18', 'W D18', 'W E18', 'W B17', 'W F17', 'W B16', 'W F16', 'W B15', 'W F15', 'W C14', 'W D14', 'W E14']
    seq4 = ['B R18', 'B S19', 'B S17', 'B T18',
            'W Q19', 'W Q18', 'W R19', 'W R17', 'W S16', 'W T17', 'W T16']
    seq5 = ['B R1', 'B R2', 'B S1', 'B S3', 'B T2', 'B T3',
            'W Q1', 'W Q2', 'W R3', 'W S4', 'W T4']
    seq = seq1 + seq2 + seq3 + seq4 + seq5
    res = board.play_seq(seq)
    eprint(board)
    eprint('res:{} ko:{}'.format(res, board.ko))
    score = board.tromp_taylor_score()
    eprint('score:{}'.format(score))

    seq = ['W D4']
    res = board.play_seq(seq)
    eprint(board)
    eprint('seq:{} res:{} ko:{}'.format(seq, res, board.ko))

    seq = ['W D10']
    res = board.play_seq(seq)
    eprint(board)
    eprint('seq:{} res:{} ko:{}'.format(seq, res, board.ko))

    seq = ['W F10']
    res = board.play_seq(seq)
    eprint(board)
    eprint('seq:{} res:{} ko:{}'.format(seq, res, board.ko))

    seq = ['W D16']
    res = board.play_seq(seq)
    eprint(board)
    eprint('seq:{} res:{} ko:{}'.format(seq, res, board.ko))

    seq = ['W S18']
    res = board.play_seq(seq)
    eprint(board)
    eprint('seq:{} res:{} ko:{}'.format(seq, res, board.ko))

    seq = ['W T19']
    res = board.play_seq(seq)
    eprint(board)
    eprint('seq:{} res:{} ko:{}'.format(seq, res, board.ko))

    seq = ['W S2']
    res = board.play_seq(seq)
    eprint(board)
    eprint('seq:{} res:{} ko:{}'.format(seq, res, board.ko))

    seq = ['W T1']
    res = board.play_seq(seq)
    eprint(board)
    eprint('seq:{} res:{} ko:{}'.format(seq, res, board.ko))


def test_undo():
    board = Board(19)
    eprint(board)
    # SETUP
    seq1 = ['B C4', 'B D5', 'B D3', 'B E4',
            'W B4', 'W C3', 'W C5', 'W D2', 'W D6', 'W E3', 'W E5', 'W F4']
    seq2 = ['B C11', 'B D11', 'B E11', 'B F11', 'B G11', 'B C10', 'B E10', 'B G10', 'B C9', 'B D9', 'B E9', 'B F9',
            'B G9',
            'W C12', 'W D12', 'W E12', 'W F12', 'W G12', 'W B11', 'W H11', 'W B10', 'W H10', 'W B9', 'W H9', 'W C8',
            'W D8', 'W E8', 'W F8', 'W G8']
    seq3 = ['B C17', 'B D17', 'B E17', 'B C16', 'B E16', 'B C15', 'B D15', 'B E15',
            'W C18', 'W D18', 'W E18', 'W B17', 'W F17', 'W B16', 'W F16', 'W B15', 'W F15', 'W C14', 'W D14', 'W E14']
    seq4 = ['B R18', 'B S19', 'B S17', 'B T18',
            'W Q19', 'W Q18', 'W R19', 'W R17', 'W S16', 'W T17', 'W T16']
    seq5 = ['B R1', 'B R2', 'B S1', 'B S3', 'B T2', 'B T3',
            'W Q1', 'W Q2', 'W R3', 'W S4', 'W T4']
    seq = seq1 + seq2 + seq3 + seq4 + seq5
    res = board.play_seq(seq)
    eprint(board)

    for i in range(5):
        board.undo()
        eprint(board)

def test_reg():
    N=3
    board = Board(N)
    seq = ['B B2', 'W B3', 'B C1']
    res = board.play_seq(seq)
    eprint(board)
    #next move W C3
    p=cd2p('C3',board.N)
    eprint(p)
    reg=board.create_board_move_register(Color.WHITE, p)
    eprint('len reg:{}'.format(len(reg)))
    eprint(reg)
    eprint(reg[0])
    eprint(reg[1])

    eprint('GET BOARD AND MOVE FROM REGISTER')
    board2,a=Board.get_board_and_move_from_register_str(N, str(reg), Color.WHITE)
    eprint(board2)
    eprint(utils.p2cd(utils.a2p(a,N),N))
    board2.play(Color.WHITE,utils.a2p(a,N))
    eprint(board2)

def test_eye():
    N = 9
    board = Board(N)
    seq1 = ['B C4', 'B D3', 'B D5', 'B E4',
            'W E6', 'W F5', 'W F7', 'W G6']
    board.play_seq(seq1)
    eprint(board)

    seq2=['B D4','W D4','B F6','W F6','B E5','W E5']

    for mov in seq2:
        c,p=utils.c_cd2cp(mov,N)
        eprint(c,p)
        eprint('mov:{} is_my_eye:{}'.format(mov, board.is_my_eye(c, p)))

#    seq = ['B B2', 'W B3', 'B C1']


if __name__ == '__main__':
    # test_init()
    # test_capture()
    # test_suicide()
    #test_play_seq()
    #test_ko()
    # test_score()
    # test_inf_play()
    # test_nonempty()
    # test_get_group()
    # test_eyes()
    #test_undo()
    #test_reg()
    #board=Board(9)
    #print(board)

    test_eye()
    # test_str()


