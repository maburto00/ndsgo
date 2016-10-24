# from board import Board
# from gomill.boards import Board
from board import Board
from lookup_players import MCPlayerQ
from player import HumanPlayer
from utils import Color, p2cd, eprint, player_file


class Match:
    def __init__(self, N, p1, p2, verbose=False):
        # TODO: p1 should be the player with black unless there is a handicap
        # TODO: implement handicap
        self.board = Board(N)
        self.players = [p1, p2]
        # self.p1 = p1
        # self.p2 = p2

        self.verbose = verbose
        self.steps = 0
        self.color_order = [Color.BLACK, Color.WHITE]

    def update_boards(self, mov, color):
        # print(mov)
        # eprint('mov(p):{} move:{}'.format(mov, p2cd(mov, self.board.N)))

        res1 = self.board.play(color, mov)
        res2 = self.players[(self.steps) % 2].board.play(color, mov)
        # if color == self.p1.color:
        # res2 = self.p2.board.play(color, mov)
        # else:
        #            res2 = self.p1.board.play(color, mov)

        if res1 < 0 or res2 < 0:
            eprint('Error in match.update_boards() mov:{} color:{} res1:{} res2:{} '.format(mov, color, res1, res2))

    def play_match(self):
        """ alternate play bw black and white until both pass"""
        eprint('INITIAL BOARD')
        eprint(self.board)
        # eprint(self.p1.board)
        # eprint(self.p2.board)
        num_pass = 0
        self.steps = 0
        # players = [self.p1, self.p2]

        while num_pass < 2:
            self.steps += 1
            ind = (self.steps + 1) % 2
            current_player = self.players[ind]
            color = self.color_order[ind]
            mov = current_player.genmove(color)

            if mov is not None:
                self.update_boards(mov, color)
                num_pass = 0
            else:
                num_pass += 1
            if (self.verbose):
                eprint('Move by {}: {}'.format('BLACK' if color == Color.BLACK else 'WHITE',
                                               'PASS' if mov is None else p2cd(mov, self.board.N)))
                eprint(self.board)
                # eprint(self.players[ind].board)
                # eprint(self.players[(ind + 1) % 2].board)
                # print('')

        eprint('Score: {}'.format(self.board.tromp_taylor_score()))


def test_mcplayer_vs_humanplayer(N):
    """
    test against human player
    :return:
    """
    board = Board(N)
    p1 = MCPlayerQ(N,epsilon=0)
    p1.load_Q(player_file[N])
    p2 = HumanPlayer(N)
    match = Match(N, p1, p2, verbose=True)
    match.play_match()


def test_mcplayer_vs_humanplayer_3x3():
    """
    test against human player
    :return:
    """
    board = Board(3)
    p1 = HumanPlayer(3)
    p2 = MCPlayerQ(3)
    p2.load_Q(player_file[3])
    match = Match(3, p1, p2, verbose=True)
    match.play_match()


def test_human_vs_human():
    board = Board(2)
    p1 = HumanPlayer(2)
    p2 = HumanPlayer(2)


def test_mc_vs_mc():
    board = Board(2)
    seed = 4
    verbose = True
    p1 = MCPlayerQ(2)
    p2 = MCPlayerQ(2)

    p1.new_game()
    p2.new_game()

    match = Match(2, p1, p2, verbose=verbose)
    match.play_match()

    p1.new_game()
    p2.new_game()

    match = Match(2, p1, p2, verbose=verbose)
    match.play_match()

    # print("N")
    # print(match.p1.N)
    # print("Q")
    # print(match.p1.Q)
    # match.p1.update_Q(1)
    # print("after Q")
    # print(match.p1.Q)
    eprint("steps:{}".format(match.steps))


    # board = Board(2)
    # p1 = MCPlayer(board.copy(), 'b')
    # p2 = MCPlayer(board.copy(), 'w')
    # match = Match(board.copy(), p1, p2)
    # match.play_match()
    # def multiple_match():


if __name__ == '__main__':
    # test_mc_vs_mc()
    # test_mcplayer_vs_humanplayer()
    test_mcplayer_vs_humanplayer(2)
