import time
import matplotlib.pyplot as plt
import numpy as np

from player import Player
from utils import eprint, Color, a2p, p2cd


# TODO: use UCB for exploration, because player is too weak because it doesn't explore enough


class MCPlayerQ(Player):
    """
    A player able to train with self play using loookup table for the Q values.
    We use MC RL with epsilon greedy for exploration to train the player.

    Q array description:
    The Q table is an array of n * n + 2 dimensions with shape (2, 3, 3, ... , 3, n * n + 1).
    - The first position defines the color of the player that will play(0 for BLACK and 1 for WHITE)
    - The next n * n positions define the board state. The number 3 is because we have 3 possible values
    for each intersection on the go board (Color.BLACK, Color.WHITE or Color.EMPTY').
    - The last value is number of possible actions in a given board state. It is n * n + 1 because we have n * n possible
    positions on the board where we could play and we also can pass.

    For simplicity we will use three indices for accessing the Q values:
        Q[c][s][a]
    where:
    - c is the color of the current player. 0 for BLACK and 1 for WHITE.
    - s is the board state. it is a n*n tuple containing values 0, 1, or 2 (for EMPTY, BLACK and WHITE, See utils.Color)
        e.g. for 2x2 board (0,0,0,0) is the empty board and (1,0,0,2) is the board position:   X.                                                                                    X.
                                                                                               .O
    - a is the action. it is a value from 0 to n*n, where each one indicates a position on the board or passing.
    """

    def __init__(self, N, seed=None, epsilon=0.2, verbose=False, OI=False):
        Player.__init__(self, N)

        self.player_file = {2:'MC_Q_EG_OI_N2_G1000000_seed2_epsilon50_time744.npy',
                            3:'MC_Q_EG_OI_N3_G100000_seed2_epsilon50_time315.npy'}

        # optimistic initialization
        self.OI = OI

        self.exploration_algorithm = '_EG'
        if self.OI:
            self.exploration_algorithm = '_EG_OI'


        self.seed = seed
        if seed is not None:
            np.random.seed(seed)
        self.verbose = verbose

        # See description of Q in the comments of the class
        self.Q_SHAPE = (2,) \
                  + tuple([3 for i in range(N * N)]) \
                  + (N * N + 1,)
        self.MC_Q = np.zeros(self.Q_SHAPE)
        self.MC_N = np.zeros(self.Q_SHAPE)


        if self.OI:
            self.MC_Q = np.ones(self.Q_SHAPE)
            self.MC_Q[Color.WHITE] *= -1

        self.episode_history = []
        self.epsilon = epsilon

        # total number of games played
        self.episodes = 0

        # This default values can be changed before calling self_play() to train.
        self.set_QH_parameters(QH_numQ=1000, QH_delta=1)

        self.training_time = 0

    def new_game(self):
        Player.new_game(self)
        self.episode_history = []

    def set_QH_parameters(self, QH_numQ, QH_delta):
        """
        Parameters for storing the evolution of the Q values in order to plot them
        QH (Q History) will store only "QH_numQ" Q values from every "QH_delta"-th episode
        :param QH_numQ: number of Q values that we will store (we won't store all the Q values in QH)
        :param QH_delta: defines how many episodes to skip in order to save the next batch of Q values
        :return:
        """

        self.QH_numQ = QH_numQ
        if self.MC_Q.size < self.QH_numQ:
            self.QH_numQ = self.MC_Q.size

        self.QH_delta = QH_delta

        # QH_Q_perm are the indexes for the Q values that we will store (we won't store all the Q values in QH)
        self.QH_Q_perm = np.random.permutation(range(self.MC_Q.size))[0:self.QH_numQ].copy()

        self.QH = [[] for _ in range(self.QH_numQ)]

        # Append initial values of Q
        flat_Q = self.MC_Q.flatten()
        for i in range(self.QH_numQ):
            self.QH[i].append(flat_Q[self.QH_Q_perm[i]])

    def save_Q(self, filename='Q_values'):
        np.save(filename, self.MC_Q)

    def load_Q(self, filename='Q_values.npy'):
        self.MC_Q = np.load(filename)

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
        title = 'MC_Q{}_N{}_G{}_seed{}_epsilon_{}_QHnumQ{}_time{}'.format(self.exploration_algorithm, self.board.N, (num_points - 1) * self.QH_delta,
                                                      self.seed, int(self.epsilon*100), self.QH_numQ, int(self.training_time))
        fig.canvas.set_window_title(title)

        plt.title('MC Q values')
        plt.xlabel('Episodes of self play')
        plt.ylabel('Q')

        for i in range(self.QH_numQ):
            plt.plot(t, self.QH[i], 'k-')

        plt.savefig(title)
        # plt.show()

    def _get_state(self, board_list):
        """
        Converts board representation to a tuple defining the state of the board for lookup table Q
        :param board_list:
        :return:
        """
        state_list = []
        N = self.board.N
        for i in range(N):
            ind = a2p(i * N, N)
            state_list += self.board.board[ind:ind + N]
        return tuple(state_list)

    def genmove(self, c):
        """
        Plays a move on the internal board and returns the selected move.
        Also, updates N for the s,a pair selected
        :return: (row,col) mov
        """

        N = self.board.N
        s = self._get_state(self.board.board)

        coin = np.random.random()
        # with probability epsilon choose random action, with probability 1-epsilon choose greedy action
        if coin <= self.epsilon:
            ind_actions = np.random.permutation(N * N + 1)
        else:
            if c == Color.BLACK:
                # descending order (from black perspective, we want the action which maximizes Q)
                ind_actions = sorted(range(N * N + 1),
                                     key=lambda k: -1 * self.MC_Q[c][s][k])
            else:
                # ascending order (from white perspective, we want the action which minimizes Q)
                ind_actions = sorted(range(N * N + 1),
                                     key=lambda k: self.MC_Q[c][s][k])

        if self.verbose:
            eprint("{} coin: {} {} ind: {} Q:{}".format('BLACK' if c == Color.BLACK else 'WHITE',
                                                        coin,
                                                        'RANDOM' if coin <= self.epsilon else 'ORDER',
                                                        ind_actions, self.MC_Q[c][s]))
        # try action until a legal action is completed
        for a in ind_actions:
            if a == N * N:  # pass move
                mov = None
                break
            mov = a2p(a, N)

            if self.board.ko and mov == self.board.ko:  # move is a ko so continue
                continue
            #elif self.board.is_my_eye(c, mov):
#                eprint('it is my own eye, so dont play here. color:{} mov:{}'.format(c, utils.p2cd(mov, N)))
#                continue
            else:
                res = self.board.play(c, mov)
                if res < 0:
                    # error, so try next action
                    eprint('Illegal move. res:{} color:{} move:{}. we will try the next one'.format(res, c, mov))
                    continue
                else:
                    break
        else:
            #if there are no legal moves, then pass
            eprint('No legal moves. PASSING')
            mov = None
            a=N*N

        self.episode_history.append((c, s, a))
        return mov

    def update_Q(self, G):
        """
        updates Q values
        :param G: the "return" of the episode, 1 if black wins, -1 if white wins
        :return:
        """
        for (c, s, a) in self.episode_history:
            self.MC_N[c][s][a] += 1
            self.MC_Q[c][s][a] = self.MC_Q[c][s][a] + (G - self.MC_Q[c][s][a]) / self.MC_N[c][s][a]

        # only store in QH every QH_delta iterations
        flat_Q = self.MC_Q.flatten()
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
        colors = [Color.BLACK, Color.WHITE]
        steps = 0

        while passes < 2:
            steps += 1
            if n_steps is not None and steps > n_steps:
                break
            c = colors[(steps + 1) % 2]
            mov = self.genmove(c)
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
        # we print 100 times the status of the program
        times_to_print=num_games/100
        for i in range(num_games):
            self.automatch()
            score = self.board.tromp_taylor_score()

            if i % times_to_print==0:
                eprint("i: {}, {} elements {} B {} KB {} MB {} GB".format(i,
                                                                      len(self.QH) * self.episodes,
                                                                      len(self.QH) * self.episodes * 8,
                                                                      len(self.QH) * self.episodes * 8 / 1024,
                                                                      len(self.QH) * self.episodes * 8 / (
                                                                          1024 * 1024),
                                                                      len(self.QH) * self.episodes * 8 / (
                                                                          1024 * 1024 * 1024)))
                eprint("score: {} history({}): {}".format(score, len(self.episode_history), self.episode_history))

            if self.verbose:
                eprint('Match: {} Score: {}'.format(i + 1, score))
            if score != 0:
                G = score / abs(score)
            self.update_Q(G)



def train_mcplayer(N=2, num_games=1000000, seed=None, epsilon=0.2, verbose=False,OI=False):
    """
    Play num_games games of self play on a 2x2 board and update Q values
    Then save the Q values on a file and then plot the Q values and save as an image.
    """
    mcPlayer = MCPlayerQ(N, seed=seed, epsilon=epsilon,verbose=verbose, OI=OI)

    episodes_to_plot = 1000
    QH_delta = num_games // episodes_to_plot
    if QH_delta < 1:
        QH_delta = 1

    mcPlayer.set_QH_parameters(QH_numQ=1000, QH_delta=QH_delta)

    t0 = time.time()
    mcPlayer.self_play(num_games)
    mcPlayer.training_time = time.time() - t0


    file_name = 'MC_Q{}_N{}_G{}_seed{}_epsilon{}_time{}.npy'.format(mcPlayer.exploration_algorithm, N, num_games, seed,
                                                                    int(epsilon*100), int(mcPlayer.training_time))
    eprint('e2plot:{} Qdelta:{} file:{} '.format(episodes_to_plot, QH_delta, file_name))
    mcPlayer.save_Q(file_name)

    mcPlayer.plot_QH()


def play_5_moves():
    mcPlayer = MCPlayerQ(2)
    mcPlayer.load_Q('Q_n2_N10K.npy')
    mcPlayer.automatch(6)


def play_moves_3x3(steps=5):
    mcPlayer = MCPlayerQ(3)
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
    mcPlayer = MCPlayerQ(2)
    mcPlayer.episode_history = [(0, (0, 0, 0, 0), 0),
                                (1, (1, 0, 0, 0), 3),
                                (0, (1, 0, 0, 2), 4)]

    # this is not actually true, but just for the test
    G = 1
    mcPlayer.update_Q(1)
    mcPlayer.episode_history = [(0, (0, 0, 0, 0), 0)]
    mcPlayer.update_Q(0)
    mcPlayer.episode_history = [(0, (0, 0, 0, 0), 0), (0, (1, 0, 0, 2), 4)]
    mcPlayer.update_Q(0)
    mcPlayer.plot_QH()


def test_memory(N=3):
    """
    STATUS: OK
    For different board sizes we print the memory used by the Q array
    Results:
     n = 2 . 810 elements 6480 B 6 KB 0 MB 0 GB
     n = 3 . 393660 elements 3149280 B 3075 KB 3 MB 0 GB
     n = 4 . MemoryError
    :return:
    """
    mcPlayer = MCPlayerQ(N)
    eprint("{} elements {} B {} KB {} MB {} GB".format(mcPlayer.MC_Q.size,
                                                       mcPlayer.MC_Q.nbytes,
                                                       mcPlayer.MC_Q.nbytes / 1024,
                                                       mcPlayer.MC_Q.nbytes / (1024 * 1024),
                                                       mcPlayer.MC_Q.nbytes / (1024 * 1024 * 1024)))


def test_self_play():
    """
    STATUS: ?
    Play 5 games of self play, and plot Q values
    Check that history (and other variables) are reinitialized in each game
    :return:
    """
    mcPlayer = MCPlayerQ(2)
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
    mcPlayer = MCPlayerQ(2)
    mcPlayer.automatch()
    score = mcPlayer.board.tromp_taylor_score()
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
    mcPlayer = MCPlayerQ(2)
    print(mcPlayer._get_state(mcPlayer.board))
    print(mcPlayer.board)
    pass


if __name__ == '__main__':
    # test_memory()
    # test_update_Q()
    # test_automatch()
    # test_self_play()

    #train_mcplayer(2, 10, seed=2, epsilon=0.8, verbose=True)

    # for i in [10 ** 2, 10 ** 3, 10 ** 4, 10 ** 5, 10 ** 6]:
    for i in [10 ** 7]:
        train_mcplayer(3, i, seed=2, epsilon=0.5,verbose=False,OI=True)

    # t0 = time.time()
    # train_mcplayer(3, 10 ** 7)
    # eprint('time to train:{}'.format(time.time() - t0))


    # play_5_moves()
    # test_get_state()
    # play_moves_3x3(20)
    # train_3x3_mcplayer()
    # print_random_values()
