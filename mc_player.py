import utils
from player import Player
import numpy as np
from gomill.boards import Board

class MCPlayer(Player):
    def __init__(self, board, color, epsilon=0.2):
        Player.__init__(self, board, color)
        n = board.side
        self.Q = np.zeros(tuple([3 for i in range(n * n)]) + (n * n + 1,))
        self.N = np.zeros(tuple([3 for i in range(n * n)]) + (n * n + 1,))
        self.history = []
        self.epsilon = epsilon
        # TODO: try, intead of using a ndarray of rank 16, use a matrix of shape (43046721,17)
        # and the first number should be converted from base-10 to base-3 to intepredte the state.

    def _get_state(self, board_list):
        board_flat = map(utils.letter2int, [item for sublist in board_list for item in sublist])
        return tuple(board_flat)

    def genmove(self):
        """
        :return: (row,col) mov
        """
        s = self._get_state(self.board.board)
        coin = np.random.random()
        n = self.board.side

        if (coin <= self.epsilon):  # with probability epsilon choose random action
            ind_actions = np.random.permutation(n * n + 1)
        else:  # with probability 1-epsilon choose the greedy action
            ind_actions = sorted(range(n * n + 1), key=lambda k: self.Q[s][k])  # all actions ordered from best to worst
        #print("coin: {} ind: {}".format(coin,ind_actions))
        # try action until legal action is completed
        for a in ind_actions:
            #TODO: if move is equal to n*n, then it is a PASS move)
            if a==n*n: #pass move
                mov=None
                break
            mov = utils.z_to_xy(a, n)
            if self.ko and mov==self.ko: #move is a ko so continue
                continue
            else:
                try:
                    state_action_pair = tuple([s, a])
                    (row, col) = utils.z_to_xy(a, n)
                    self.ko = self.board.play(row, col, self.color)
                    break
                except(ValueError):
                    # HEURISTIC: automatically give negative value to Q in that state if it is an illegal move
                    #print("ValueError exception")
                    self.Q[s][a] = -1
                    continue
        #actualizar N
        self.N[s][a] += 1
        self.history.append((s,a))
        return mov

    def update_Q(self,G):
        for (s,a) in self.history:
            self.Q[s][a]=self.Q[s][a]+(G-self.Q[s][a])/self.N[s][a]


def test_mcplayer():
    """
    Basic test, play against random player...
    :return:
    """
    board = Board(2)
    player = MCPlayer(board, 'b')
    pos = player.genmove()
    print(pos)
    print(player.board)
    print(player.history)
    print("N")
    print(player.N)
    print("Q")
    print(player.Q)
    player.update_Q(1)
    print("after Q")
    print(player.Q)
    pass




if __name__ == '__main__':
    test_mcplayer()
