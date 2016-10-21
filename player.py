import numpy as np

from board import Board
from utils import Color, cd2p, a2p, eprint


class Player:
    """
    Base class for all the players. We have the following types of players:
    - Basic player (implemented here) e.g. HumanPlayer, RandomPlayer
    - Lookup player. Using tables for MC,TD and TD(lambda)
    - param players. Using function approximation for MC,TD and TD(lambda)
    - cnn players.
    - mcts player.
    - ...
    """

    def __init__(self, board, color=Color.BLACK):
        self.board = board
        self.color = color
        # self.ko = None

    def new_game(self):
        # TODO: See gtp draft (maybe we have to reset other things
        self.board.clear_board()
        # self.ko = None

    def genmove(self, color):
        return None


class RandomPlayer(Player):
    def genmove(self, color):
        n = self.board.N
        ind_actions = np.random.permutation(n * n + 1)

        for a in ind_actions:
            if a == n * n:  # pass move
                mov = None
                break
            mov = a2p(a, n)

            if self.board.ko and mov == self.board.ko:  # move is a ko so continue
                continue

            else:
                res = self.board.play(color, mov)
                if res < 0:
                    # error, so try next action
                    continue
                else:
                    break
        return mov


class HumanPlayer(Player):
    def genmove(self, color):
        """
        the user inputs the move in the form A1 or B2, etc...
        :return: position p, or None for pass
        """
        # move_t = input("Enter move (e.g: 0,0 or None for passing): ")
        # TODO: do in while in order to catch exceptions and manage ko
        eprint("Enter move (e.g: A1 or '' for passing): ", end='')
        mov = raw_input()

        if mov == '':
            return None

        p = cd2p(mov, self.board.N)
        self.board.play(color, p)

        return p

        # def update_board(p1,p2,mov):
        #   human_player.board.play(mov)


def test_random_player():
    board = Board(3)
    player = RandomPlayer(Board(4), Color.BLACK)
    colors = [Color.BLACK, Color.WHITE]
    for i in range(5):
        color = colors[i % 2]
        p = player.genmove(color)
        if p is not None:
            player.board.play(color, p)
        else:
            eprint('pass')
        eprint(player.board)


def test_human_player():
    board = Board(4)
    p1 = HumanPlayer(Board(4), Color.BLACK)
    eprint(p1.board)
    mov = p1.genmove(p1.color)
    eprint('mov:{}'.format(mov))
    res = p1.board.play(p1.color, mov)
    eprint(p1.board)
    eprint('res:{}'.format(res))


if __name__ == '__main__':
    # main()
    # test_human_player()
    test_random_player()
