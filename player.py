# import numpy as np
import random
from boards import Board


# def board2int(board_array):
#     state=0
#     #basically we are converting from base-3 to decimal
#     n=board.side
#     for i in range(n):
#         for j in range(n):
#             pos = (n * i + j)
#             if board.board[pos]=='b':
#                 state = state + ((3**pos) * 1)
#             elif board.board[pos]=='w':
#                 state = state + ((3 ** pos) * 2)
#     return state
#
# def tup2num(t, n):
#     return n*t[0] + t[1]

class Player:
    """
        actions go from 0 to n*n, where
        v #table for the value function
        q #table for the value function
    """

    def __init__(self, board, color='b'):
        self.board = board
        self.color = color
        # v = np.zeros(tuple([3 for i in range(n*n)]))
        # q = np.zeros(tuple([3 for i in range(n * n)])+(16,))
        # TODO: try, intead of using a ndarray of rank 16, use a matrix of shape (43046721,16)
        # and the first number should be converted from base-10 to base-3 to intepredte the state.

    def make_move(self):
        pass

    def update_board(self, x, y, color):
        try:
            self.board.play(x, y, color)
        except Exception:
            print('There was an exception in update board randomplayer')

    def update_v(self):
        pass

    def save_v(self):
        pass


class RandomPlayer(Player):
    def make_move(self):
        available_pos = self.board.get_available_pos()
        len_a = len(available_pos)
        r = random.randint(0, len_a)
        if r == len_a:
            return None
        else:
            return available_pos[r]


# class PlayerMC(Player):
#     def _get_state(board):
#         state=0
#         state=
#
#     def make_move(self):
#         state=_get_state(board)
#
#     pass
#
# class PlayerTD(Player):
#     pass

class HumanPlayer(Player):
    def make_move(self):
        """
            the user inputs a tuple with the coordinates for the move
        :return: a tuple with the move, or None for pass
        """
        # move_t = input("Enter move (e.g: 0,0 or None for passing): ")
        mov = raw_input("Enter move (e.g: 0,0 or '' for passing):")
        if mov == '':
            return None
        return tuple([int(x) for x in mov.split(',')])

        # def update_board(p1,p2,mov):
        #   human_player.board.play(mov)


def main_human():
    board = Board(4)
    p1 = HumanPlayer(board.copy(), 'b')
    mov = p1.make_move()
    print(mov)


def main():
    """test for player"""
    board = Board(4)
    # p1 = RandomPlayer(board.copy(), 'w')
    # p2 = RandomPlayer(board.copy(), 'b')

    pass
    print('hola')
    print('adios')
    # human_player=HumanPlayer(board.copy(),'w')
    # cpu_player = Player(board.copy(), 'b')
    #
    # while True:
    #     #black plays
    #     mov=human_player.play()
    #     board.play(mov)
    #
    #     #white plays
    #     mov=cpu_player.play()
    #     human_player.board.play(mov)
    #     cpu_player.board.play(mov)


if __name__ == '__main__':
    # main()
    main_human()
