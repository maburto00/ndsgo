import numpy as np
import utils
# from board import Board
from gomill.boards import Board


#TODO: create class MCPlayer
#TODO: (in the long term) create our own Board and GTP implementations

# def board2int(board_array):
#     state=0
#     #basically we are converting from base-3 to decimal
#     n=board.N
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
        self.ko = None

    def clear_board(self):
        self.board = Board(self.board.N)
        self.ko = None
        self.history = []

    def genmove(self,color):
        print('in player genmove')
        return None

    def play(self, color, x, y):

        try:
            self.board.play(x, y, color)
        except Exception:
            print('There was an exception in update board for player class')

    def update_v(self):
        pass

    def save_v(self):
        pass


# class RandomPlayer(Player):
#     def genmove(self):
#         available_pos = self.board.get_available_pos()
#         len_a = len(available_pos)
#         r = random.randint(0, len_a)
#         if r == len_a:
#             return None
#         else:
#             return available_pos[r]
#
# class FixedPlayer(Player):
#
#     def __init__(self, board, color='b'):
#         Player.__init__(self, board, color)
#         fixed_moves = [()]
#         move_num = 0
#
#     def genmove(self):
#         return (0,0)
#


class PlayerTD(Player):
    pass

class HumanPlayer(Player):
    def genmove(self, color):
        """
        the user inputs a tuple with the coordinates for the move
        :return: a tuple with the move, or None for pass
        """
        # move_t = input("Enter move (e.g: 0,0 or None for passing): ")
        #TODO: do in while in order to catch exceptions and manage ko

        mov = raw_input("Enter move (e.g: 0,0 or '' for passing):")

        if mov == '':
            return None
        return tuple([int(x) for x in mov.split(',')])

        # def update_board(p1,p2,mov):
        #   human_player.board.play(mov)

def main_human():
    board = Board(4)
    p1 = HumanPlayer(board.copy(), 'b')
    mov = p1.genmove()
    print(mov)


def main():
    """test for player"""
    print('main')
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
    main()

