import numpy as np
import matplotlib.pyplot as plt
import time

from utils import eprint, Color, a2p, p2cd
from player import Player

# TODO: Do a better planning of classes and files (maybe we can put all of the players in the player.py file)
# TODO: and just put comments like this ############# to separate MC, TD, etc...
# TODO: Store N table also in order to be able to stop and restart training

from board import Board


# TODO: use our own Board implementation using [Muller 2002] conventions

class MCPlayerQ(Player):
    """
    A player able to train with self play using loookup table for the Q values.
    We use MC RL with epsilon greedy for exploration to train the player.

    Q array description:
    The Q table is an array of n * n + 2 dimensions with shape (2, 3, 3, ... , 3, n * n + 1).
    - The first position defines the color of the player that will play(0 for BLACK and 1 for WHITE)
    - The next n * n positions define the board state. This is because we have 3 possible values
    for each intersection of the go board (Color.BLACK, Color.WHITE or Color.EMPTY').
    - The last value is number of possible actions in a given board state. It is n * n + 1 because we have n * n possible
    positions on the board where we could play and we also can pass.

    For simplicity we will use three indices for accesing the Q values:
        Q[c][s][a]
    where:
    - c is the color of the current player. 0 for BLACK and 1 for WHITE.
    - s is the board state. it is a n*n tuple containing values 0, 1, or 2 (for EMPTY, BLACK and WHITE, See utils.Color)
        e.g. for 2x2 board (0,0,0,0) is the empty board and (1,0,0,2) is the board position:   X.                                                                                    X.
                                                                                               .O
    - a is the action. it is a value from 0 to n*n, where each one indicates a position on the board or passing.
    """

    # TODO: move test methods to test_MCPlayerQ.py
    def __init__(self, board, color, epsilon=0.2, seed=None, verbose=False):
        # TODO: Board should be local, then use method set_board() to change it in case of handicap or something
        Player.__init__(self, board, color)
        n = board.N

        self.seed = seed
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

    def clear_board(self):
        Player.clear_board(self)
        self.history = []

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

        # In t=0 we have the initial values, then we have the values stored from update_Q()
        t = [0] + [i * self.QH_delta + 1 for i in range(num_points - 1)]

        fig = plt.figure()
        title = 'MC Q history N{} G{} QHnumQ{} seed{}'.format(self.board.N, (num_points - 1) * self.QH_delta,
                                                              self.QH_numQ, self.seed)
        fig.canvas.set_window_title(title)

        plt.title('MC Q values')
        plt.xlabel('Episodes of self play')
        plt.ylabel('Q')

        for i in range(self.QH_numQ):
            plt.plot(t, self.QH[i], 'k-')
            # plt.plot(t, self.QH[i])
        plt.savefig(title)
        plt.show()

    def _get_state(self, board_list):
        """
        Converts board representation to a tuple defining the state of the board for lookup table Q
        :param board_list:
        :return:
        """
        state_list = []
        n = self.board.N
        for i in range(n):
            ind = a2p(i * n, n)
            state_list += self.board.board[ind:ind + n]
        return tuple(state_list)

    def genmove(self, color):
        # TODO: call super() See: http://blog.thedigitalcatonline.com/blog/2014/05/19/method-overriding-in-python/#.V-YIDSjhDcc

        """
        Plays a move on the internal board and returns the selected move.
        Also, updates N for the s,a pair selected
        :return: (row,col) mov
        """
        # TODO: genmove should not update Q all the time, create fn that does this and call genmove to generate move
        n = self.board.N
        # IMPORTANT, don't use utils.Color for this, since black would be 1 and white 2
        c = 0 if color == Color.BLACK else 1
        s = self._get_state(self.board.board)

        coin = np.random.random()
        # with probability epsilon choose random action, with probability 1-epsilon choose greedy action
        if coin <= self.epsilon:
            ind_actions = np.random.permutation(n * n + 1)
        else:
            # See -1. the return G is 1 if black wins and 0 if white wins, so best action is different if player is WHITE
            if color == Color.BLACK:
                # descending order (from black perspective, we want the action which maximizes Q)
                ind_actions = sorted(range(n * n + 1),
                                     key=lambda k: -1 * self.Q[c][s][k])
            else:
                # ascending order ((from white perspective, we want the action which minimizes Q)
                ind_actions = sorted(range(n * n + 1),
                                     key=lambda k: self.Q[c][s][k])

        if self.verbose:
            eprint("{} coin: {} {} ind: {} Q:{}".format('BLACK' if color == Color.BLACK else 'WHITE',
                                                        coin,
                                                        'RANDOM' if coin <= self.epsilon else 'ORDER',
                                                        ind_actions, self.Q[c][s]))
        # try action until legal action is completed
        for a in ind_actions:
            if a == n * n:  # pass move
                mov = None
                break
            # mov = z2xy(a, n)
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
        self.clear_board()

        passes = 0
        colors = [Color.BLACK, Color.WHITE]
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
                eprint('Move by {}: {}'.format('BLACK' if c == Color.BLACK else 'WHITE',
                                               'PASS' if mov is None else p2cd(mov, self.board.N)))
                eprint(self.board)
                eprint('')

    def self_play(self, num_games):
        """
        Play num_games times  against itself and learn Q values
        :param num_games:
        :return:
        """
        for i in range(num_games):
            # if self.verbose:
            eprint("i: {}, {} elements {} B {} KB {} MB {} GB".format(i,
                                                                      len(self.QH) * self.episodes,
                                                                      len(self.QH) * self.episodes * 8,
                                                                      len(self.QH) * self.episodes * 8 / 1024,
                                                                      len(self.QH) * self.episodes * 8 / (
                                                                          1024 * 1024),
                                                                      len(self.QH) * self.episodes * 8 / (
                                                                          1024 * 1024 * 1024)))
            self.automatch()
            # if self.verbose:


            score = self.board.score()
            eprint("score: {} history({}): {}".format(score, len(self.history), self.history))
            if self.verbose:
                eprint('Match: {} Score: {}'.format(i + 1, score))
            if score != 0:
                G = score / abs(score)
            self.update_Q(G)


def train_mcplayer(N=2, num_games=1000000, seed=2):
    """
    Play N=1000 games of selfplay on 2x2 board and update Q values
    Then store the Q values on file 'Q_1000.npy'
    See plot of Q values.
    :return:
    """
    # TODO: define QH_delta as a function of the number of games
    # TODO: use the seed when we want the same graphics for 100,1000,... games of selfplay
    # TODO: remove seed for general training.
    mcPlayer = MCPlayerQ(Board(N), Color.BLACK, epsilon=0.2, seed=seed, verbose=False)

    episodes_to_plot = 1000
    QH_delta = num_games // episodes_to_plot
    if QH_delta < 1:
        QH_delta = 1

    mcPlayer.set_QH_parameters(QH_numQ=1000, QH_delta=QH_delta)
    mcPlayer.self_play(num_games)

    file_name = 'MC_Q_N{}_G{}_seed{}.npy'.format(N, num_games, seed)
    eprint('e2plot:{} Qdelta:{} file:{} '.format(episodes_to_plot, QH_delta, file_name))
    mcPlayer.save_Q(file_name)

    mcPlayer.plot_QH()


def play_5_moves():
    mcPlayer = MCPlayerQ(Board(2), Color.BLACK, epsilon=0, seed=None, verbose=True)
    mcPlayer.load_Q('Q_n2_N10K.npy')
    mcPlayer.automatch(6)


def play_moves_3x3(steps=5):
    mcPlayer = MCPlayerQ(Board(3), Color.BLACK, epsilon=0, seed=None, verbose=True)
    mcPlayer.load_Q('MC_Q_N3_G1000000_seed2.npy')
    mcPlayer.automatch(steps)


def test_update_Q():
    """
    STATUS: OK
    Create fixed history and call update_Q
    history:

    ..    X.    X.    X.
    ..    ..    .O    .O
          A2    B1    pass

    Elements of history are of the form: (c, s, a)
      c can take value 0 for BLACK and 1 for WHITE
      s is of the form (0,1,....,n*n-1)
      a takes values 0,1,... and n*n where n*n is passing
    :return:
    """
    mcPlayer = MCPlayerQ(Board(2), Color.BLACK, epsilon=0.2, seed=1, verbose=True)
    mcPlayer.history = [(0, (0, 0, 0, 0), 0),
                        (1, (1, 0, 0, 0), 3),
                        (0, (1, 0, 0, 2), 4)]

    # this is not actually true, but just for the test
    G = 1
    mcPlayer.update_Q(1)
    mcPlayer.history = [(0, (0, 0, 0, 0), 0)]
    mcPlayer.update_Q(0)
    mcPlayer.history = [(0, (0, 0, 0, 0), 0), (0, (1, 0, 0, 2), 4)]
    mcPlayer.update_Q(0)
    mcPlayer.plot_QH()


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
    mcPlayer = MCPlayerQ(Board(n), Color.BLACK, epsilon=0.2, seed=1, verbose=True)
    eprint("{} elements {} B {} KB {} MB {} GB".format(mcPlayer.Q.size,
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
    mcPlayer = MCPlayerQ(Board(2), Color.BLACK, epsilon=0.2, seed=1, verbose=False)
    mcPlayer.self_play(5)
    mcPlayer.plot_QH()


def test_automatch():
    """
    STATUS: OK
    Play an automatch with seed=1, and plot Q values
    Test:
    ? 1) The printed game and the self.history variable correspond to each other
    ? 2) Play a second match and check the same as in test 1
    :return:
    """
    mcPlayer = MCPlayerQ(Board(2), Color.BLACK, epsilon=0.2, seed=2, verbose=False)
    mcPlayer.automatch()
    score = mcPlayer.board.score()
    eprint('Score: {}'.format(score))
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
        eprint('')
        eprint('seed({})'.format(iter))
        np.random.seed(iter)
        list1 = []
        for i in range(10):
            list1.append(np.random.random())

        np.random.seed(1)
        list2 = []
        for i in range(10):
            list2.append(np.random.permutation(2 * 2 + 1))

        for i in range(10):
            eprint("{:>5} {:>20} {:>15}".format(i + 1, list1[i], list2[i]))


def test_get_state():
    mcPlayer = MCPlayerQ(Board(2), Color.BLACK, epsilon=0.2, seed=2, verbose=True)
    mcPlayer._get_state(mcPlayer.board)


if __name__ == '__main__':
    # test_memory()
    # test_update_Q()
    # test_automatch()
    # test_self_play()

    # for i in [10 ** 2, 10 ** 3, 10 ** 4, 10 ** 5, 10 ** 6]:
    #    train_mcplayer(2, i)

    t0 = time.time()
    train_mcplayer(3, 10 ** 7)
    eprint('time to train:{}'.format(time.time() - t0))
    # play_5_moves()
    # test_get_state()
    # play_moves_3x3(20)
    # train_3x3_mcplayer()
    # print_random_values()
