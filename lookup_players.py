import numpy as np
import matplotlib.pyplot as plt
from utils import Color, xy_to_z, z_to_xy, letter2int
from player import Player

# TODO: Do a better planning of classes and files (maybe we can put all of the players in the player.py file)
# TODO:    and just put comments like this ############# to separate MC, TD, etc...

from gomill.boards import Board


# TODO: use our own Board implementation using [Muller 2002] conventions

class MCPlayerQ(Player):
    """
    A player able to train with self play using loookup table for the Q values.
    We use MC RL with epsilon greedy for exploration to train the player.

    Q array description:
    The Q table is an array of n * n + 2 dimensions with shape (2, 3, 3, ... , 3, n * n + 1).
    - The first position defines the color of the player that will play(0 for 'b' and 1 for 'w')
    - The next n * n positions define the board state. This is because we have 3 possible values
    for each intersection of the go board ('b' 'w' or None (empty)).
    - The last value is number of possible actions in a given board state. It is n * n + 1 because we have n * n possible
    positions on the board where we could play and we also can pass.

    For simplicity we will use three indices for accesing the Q values:
        Q[c][s][a]
    where:
    - c is the color of the current player. 0 for 'b' and 1 for 'w'.
    - s is the board state. it is a n*n tuple containing values 0, 1, or 2 (for None, 'b' and 'w', See utils.Color)
        e.g. for 2x2 board (0,0,0,0) is the empty board and (1,0,0,2) is the board position:   X.                                                                                    X.
                                                                                               .O
    - a is the action. it is a value from 0 to n*n, where each one indicates a position on the board or passing.
    """

    # TODO: move test methods to test_MCPlayerQ.py
    def __init__(self, board, color, epsilon=0.2, seed=None, verbose=False):
        # TODO: Board should be local, then use method set_board() to change it in case of handicap or something
        Player.__init__(self, board, color)
        n = board.side

        if seed is not None:
            np.random.seed(seed)
        self.verbose = verbose

        # See description of Q in the comments of the class
        Q_SHAPE = (2,) \
                  + tuple([3 for i in range(n * n)]) \
                  + (n * n + 1,)
        self.Q = np.zeros(Q_SHAPE)
        # self.Q = np.random.random(Q_SHAPE)
        self.N = np.zeros(Q_SHAPE)

        self.history = []
        self.epsilon = epsilon

        # total number of games played
        self.episodes = 0

        # This default values can be changed before calling self_play() to train.
        self.set_QH_parameters(QH_numQ=1000, QH_delta=1)

    def set_QH_parameters(self, QH_numQ, QH_delta):
        """
        Parameters for storing the evolution of the Q values in order to plot them
        QH will store only "QH_numQ" Q values from every "QH_delta"-th episode
        :param QH_numQ: number of Q values that we will store (we won't store all the Q values in QH)
        :param QH_delta: defines how many episodes to skip in order to save the next batch of Q values
        :return:
        """

        self.QH_numQ = QH_numQ
        if self.Q.size < self.QH_numQ:
            self.QH_numQ = self.Q.size

        self.QH_delta = QH_delta

        # QH_Q_perm are the indexes for the Q values that we will store (we won't store all the Q values in QH)
        self.QH_Q_perm = np.random.permutation(range(self.Q.size))[0:self.QH_numQ].copy()

        self.QH = [[] for _ in range(self.QH_numQ)]

        # Append initial values of Q
        flat_Q = self.Q.flatten()
        for i in range(self.QH_numQ):
            self.QH[i].append(flat_Q[self.QH_Q_perm[i]])

    def new_game(self, board=None, color=None):
        """
        Reset all the necessary variables for a new game:
        - board, color, ko
        - history
        :return:
        """

        if board is None:
            self.board = Board(self.board.side)
        else:
            self.board = board

        if color is None:
            self.color = self.color
        else:
            self.color = color

        self.ko = None
        self.history = []

    def save_Q(self, filename='Q_values'):
        np.save(filename, self.Q)

    def load_Q(self, filename='Q_values.npy'):
        self.Q = np.load(filename)

    def plot_QH(self):
        """
        Plot evolution over time of (some of) the Q values.
        :param num_points: the number of equally distant points (on number of episodes) we want to plot from Q_history
        :return:
        """
        num_points = len(self.QH[0])
        # if num_points < num_episodes:
        #     delta = num_episodes / num_points
        # else:
        #     delta = 1

        # In t=0 we have the initial values, then the values stored from update_Q()
        t = [0] + [i * self.QH_delta + 1 for i in range(num_points - 1)]

        for i in range(self.QH_numQ):
            # plt.plot(t, self.QH[i],'b-')
            plt.plot(t, self.QH[i])
        plt.show()

    def _get_state(self, board_list):
        """
        Converts board representation to a tuple defining the state of the board for lookup table Q
        :param board_list:
        :return:
        """
        # TODO: when we implement our own board this should change
        board_flat = map(letter2int, [item for sublist in board_list for item in sublist])
        return tuple(board_flat)

    def genmove(self, color):
        # TODO: call super() See: http://blog.thedigitalcatonline.com/blog/2014/05/19/method-overriding-in-python/#.V-YIDSjhDcc
        """
        Plays a move on the internal board and returns the selected move.
        Also, updates N for the s,a pair selected
        :return: (row,col) mov
        """
        # TODO: genmove should not update Q all the time, create fn that does this and call genmove to generate move
        n = self.board.side
        # IMPORTANT, don't use utils.Color for this, since black would be 1 and white 2
        c = 0 if color == 'b' else 1
        s = self._get_state(self.board.board)

        coin = np.random.random()
        # with probability epsilon choose random action, with probability 1-epsilon choose greedy action
        if coin <= self.epsilon:
            ind_actions = np.random.permutation(n * n + 1)
        else:
            # See -1. the return G is 1 if black wins and 0 if white wins, so best action is different if player is 'w'
            if color == 'b':
                # descending order (from black perspective, we want the action which maximizes Q)
                ind_actions = sorted(range(n * n + 1),
                                     key=lambda k: -1 * self.Q[c][s][k])
            else:
                # ascending order ((from white perspective, we want the action which minimizes Q)
                ind_actions = sorted(range(n * n + 1),
                                     key=lambda k: self.Q[c][s][k])

        if self.verbose:
            print("{} coin: {} {} ind: {} Q:{}".format('BLACK' if color == 'b' else 'WHITE',
                                                       coin,
                                                       'RANDOM' if coin <= self.epsilon else 'ORDER',
                                                       ind_actions, self.Q[c][s]))
        # try action until legal action is completed
        for a in ind_actions:
            if a == n * n:  # pass move
                mov = None
                break
            mov = z_to_xy(a, n)
            if self.ko and mov == self.ko:  # move is a ko so continue
                continue
            else:
                try:
                    (row, col) = mov
                    self.ko = self.board.play(row, col, color)
                    break
                except ValueError:
                    # HEURISTIC: automatically give -10 or +10 value to Q in that state if it is an illegal move
                    # TODO: do the same for the rotation invariant and other invariants...
                    # print("ValueError exception")
                    if color == 'b':
                        self.Q[c][s][a] = -10
                    else:
                        self.Q[c][s][a] = 10
                    continue
        self.history.append((c, s, a))
        return mov

    def update_Q(self, G):
        """
        updates Q values
        :param G: the "return" of the episode, 1 if black wins, -1 if white wins
        :return:
        """
        # TODO: exploit symmetries, rotation invariance
        for (c, s, a) in self.history:
            self.N[c][s][a] += 1
            self.Q[c][s][a] = self.Q[c][s][a] + (G - self.Q[c][s][a]) / self.N[c][s][a]

        # only store in QH every QH_delta iterations
        flat_Q = self.Q.flatten()
        if self.episodes % self.QH_delta == 0:
            for i in range(self.QH_numQ):
                self.QH[i].append(flat_Q[self.QH_Q_perm[i]])

        self.episodes += 1

    def automatch(self, n_steps=None):
        """
        Play one match against itself. NOTE: it doesn't update Q at the end, just stores history
        :param n_steps
        :return:
        """
        # TODO: Test this function. Use Debug to see history and board of each match...
        self.new_game()

        passes = 0
        colors = ['b', 'w']
        steps = 0

        while passes < 2:
            steps += 1
            if n_steps is not None and steps > n_steps:
                break
            c = colors[(steps + 1) % 2]
            mov = self.genmove(color=c)
            if mov is not None:
                passes = 0
            else:
                passes += 1
            if (self.verbose):
                print('Move by {}: {}'.format('BLACK' if c == 'b' else 'WHITE', mov))
                print(self.board)
                print('')

    def self_play(self, num_games):
        """
        Play num_games times  against itself and learn Q values
        :param num_games:
        :return:
        """
        for i in range(num_games):
            # if self.verbose:
            print("i: {}, {} elements {} B {} KB {} MB {} GB".format(i,
                                                                     len(self.QH) * self.episodes,
                                                                     len(self.QH) * self.episodes * 8,
                                                                     len(self.QH) * self.episodes * 8 / 1024,
                                                                     len(self.QH) * self.episodes * 8 / (
                                                                         1024 * 1024),
                                                                     len(self.QH) * self.episodes * 8 / (
                                                                         1024 * 1024 * 1024)))
            self.automatch()
            # if self.verbose:
            print("history({}): {}".format(len(self.history), self.history))

            score = self.board.area_score()
            if self.verbose:
                print('Match: {} Score: {}'.format(i + 1, score))
            if score != 0:
                G = score / abs(score)
            self.update_Q(G)


def train_mcplayer():
    """
    Play N=1000 games of selfplay on 2x2 board and update Q values
    Then store the Q values on file 'Q_1000.npy'
    See plot of Q values.
    :return:
    """
    mcPlayer = MCPlayerQ(Board(2), 'b', epsilon=0.2, seed=1, verbose=False)
    mcPlayer.set_QH_parameters(QH_numQ=1, QH_delta=50)
    mcPlayer.self_play(100)
    mcPlayer.plot_QH()
    mcPlayer.save_Q('Q_n2_N100.npy')


def play_5_moves():
    mcPlayer = MCPlayerQ(Board(2), 'b', epsilon=0, seed=None, verbose=True)
    mcPlayer.load_Q('Q_n2_N100.npy')
    mcPlayer.automatch(6)


def train_3x3_mcplayer():
    """
    Play N=1000 games of selfplay on 2x2 board and update Q values
    Then store the Q values on file 'Q_1000.npy'
    See plot of Q values.
    :return:
    """
    mcPlayer = MCPlayerQ(Board(3), 'b', epsilon=0.2, seed=1, verbose=False)
    mcPlayer.self_play(200)
    mcPlayer.plot_QH()
    mcPlayer.save_Q('Q_n3_N200.npy')


def test_update_Q():
    """
    STATUS: OK
    Create fixed history and call update_Q
    history:

    ..    X.    X.    X.    X.
    ..    ..    .O    .O    .O
          A2    B1    pass  pass

    Elements of history are of the form: (c, s, a)
      c can take value 0 for 'b' and 1 for 'w'
      s is of the form (0,1,....,n*n-1)
      a takes values 0,1,... and n*n where n*n is passing
    :return:
    """
    mcPlayer = MCPlayerQ(Board(2), 'b', epsilon=0.2, seed=1, verbose=True)
    mcPlayer.history = [(0, (0, 0, 0, 0), 0),
                        (1, (1, 0, 0, 0), 3),
                        (0, (1, 0, 0, 2), 4),
                        (0, (1, 0, 0, 2), 4)]

    # this is not actually true, but just for the test
    G = 1
    mcPlayer.update_Q(1)
    mcPlayer.history = [(0, (0, 0, 0, 0), 0)]
    mcPlayer.update_Q(0)
    mcPlayer.update_Q(0)
    mcPlayer.plot_QH()
    #                     (1,())]


def test_memory(n=3):
    """
    STATUS: OK
    For different board sizes we print the memory used by the Q array
    Results:
     n = 2 . 810 elements 6480 B 6 KB 0 MB 0 GB
     n = 3 . 393660 elements 3149280 B 3075 KB 3 MB 0 GB
     n = 4 . MemoryError
    :return:
    """
    mcPlayer = MCPlayerQ(Board(n), 'b', epsilon=0.2, seed=1, verbose=True)
    print("{} elements {} B {} KB {} MB {} GB".format(mcPlayer.Q.size,
                                                      mcPlayer.Q.nbytes,
                                                      mcPlayer.Q.nbytes / 1024,
                                                      mcPlayer.Q.nbytes / (1024 * 1024),
                                                      mcPlayer.Q.nbytes / (1024 * 1024 * 1024)))


# TODO: create folder tests and move all mc player tests to file mcplayer_tests.py

def test_self_play():
    """
    STATUS: ?
    Play 5 games of self play, and plot Q values
    Check that history (and other variables) are reinitialized in each game
    :return:
    """
    mcPlayer = MCPlayerQ(Board(2), 'b', epsilon=0.2, seed=1, verbose=False)
    mcPlayer.self_play(5)
    mcPlayer.plot_QH()


def test_automatch():
    """
    STATUS: ?
    Play an automatch with seed=1, and plot Q values
    Test:
    ? 1) The printed game and the self.history variable correspond to each other
    ? 2) Play a second match and check the same as in test 1
    :return:
    """
    mcPlayer = MCPlayerQ(Board(2), 'b', epsilon=0.2, seed=2, verbose=True)
    mcPlayer.automatch()
    score = mcPlayer.board.area_score()
    print('Score: {}'.format(score))
    if score != 0:
        G = score / abs(score)
    mcPlayer.update_Q(G)
    mcPlayer.plot_QH()


def print_random_values():
    """
    using seed(1) print random values for random() and for permutation()
    for the first 10 times
    :return:
    """
    for iter in range(11):
        print('')
        print('seed({})'.format(iter))
        np.random.seed(iter)
        list1 = []
        for i in range(10):
            list1.append(np.random.random())

        np.random.seed(1)
        list2 = []
        for i in range(10):
            list2.append(np.random.permutation(2 * 2 + 1))

        for i in range(10):
            print("{:>5} {:>20} {:>15}".format(i + 1, list1[i], list2[i]))


def test_mcplayer_genmoves_history():
    """
    Basic test, play against fixed player...
    STATUS:
    :return:
    """
    np.random.seed(1)

    board = Board(2)
    player = MCPlayerQ(board, 'b')
    for i in range(10):
        # pos = player.genmove
        print(pos)
        print(player.board)
    print(player.history)
    # print("N")
    # print(player.N)
    # print("Q")
    # print(player.Q)
    # player.update_Q(1)
    # print("after Q")
    # print(player.Q)
    # pass


if __name__ == '__main__':
    # test_memory()
    # test_update_Q()
    # test_automatch()
    # test_self_play()
    train_mcplayer()
    # play_5_movs()
    # train_3x3_mcplayer()
    # print_random_values()
