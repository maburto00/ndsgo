from player import Player
#from board import NUM_CHANNELS
import tensorflow as tf
import numpy as np
import utils
from utils import Color, eprint
import os

from cnn_models import cnn

class CNNPlayer(Player):
    """
    CNN player

    """
    # def __init__(self, N, seed=None, epsilon=0.2, verbose=False, OI=False):
    def __init__(self, N, verbose=False):
        Player.__init__(self, N)

        dir_name='/home/mario/Dropbox/PycharmProjects/ndsgo'
        self.player_file = {9: os.path.join(dir_name,'model_9x9_l13_26000'),
                            #9: os.path.join(dir_name, 'model_9x9'),
                            #19: os.path.join(dir_name,'model_19x19_k128')}
                                19: os.path.join(dir_name, 'model_19x19_l13')}
                            #19: os.path.join(dir_name,'model_19x19')}

        self.verbose = verbose
        boardsize = N

        #with open(self.player_file[boardsize]+'.prop','r') as f:
            #self.num_channels=int(f.readline().split(',')[1])

        self.num_channels=4

        self.data = tf.placeholder(tf.float32, [1, boardsize, boardsize, self.num_channels])

        self.logits = cnn.inference_layer(self.data, boardsize, self.num_channels,11)
        #self.logits = cnn.inference(self.data, boardsize, self.num_channels)
        self.sm_output = tf.nn.softmax(self.logits)

        # init = tf.initialize_all_variables()
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)


        saver = tf.train.Saver()
        self.sess = tf.Session()
        #self.sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))
        #self.sess = tf.Session(config=tf.ConfigProto(log_device_placement=False, gpu_options=gpu_options))
        try:
            file_name = self.player_file[N]
        except:
            eprint('There is no file for boardsize {}'.format(N))
            exit()
        saver.restore(self.sess, file_name+'.ckpt')

#    def new_game(self):
 #       Player.new_game(self)

    def genmove(self, c):
        """
        Plays a move on the internal board and returns the selected move.
        Also, updates N for the s,a pair selected
        :return: (row,col) mov
        """
        # get data
        board_reg_str = str(self.board.create_board_register(c,self.num_channels))

        # data = data.reshape(num_images, NUM_CHANNELS, IMAGE_SIZE, IMAGE_SIZE)
        # data = data.transpose(0, 2, 3, 1)
        boardsize = self.board.N
        N = self.board.N

        b_data = np.frombuffer(board_reg_str, dtype=np.uint8)
        b_data = b_data.astype(np.float32)
        b_data = b_data.reshape(1, self.num_channels, boardsize, boardsize)
        # print(b_data)
        b_data = b_data.transpose(0, 2, 3, 1)
        # print(b_data)

        # predict output
        output = self.sess.run(self.sm_output, feed_dict={self.data: b_data})
        # a = np.argmax(output)
        # print(output, utils.p2cd(utils.a2p(a, boardsize), boardsize))
        # get top 5 prediction
        # top_5 = output[0].argsort()[::-1][:5]
        # print(top_5)
        # for e in top_5:
        #    print(utils.p2cd(utils.a2p(e, boardsize), boardsize))

        ind_actions = output[0].argsort()[::-1]

        ind_actions_cd=[utils.a2cd(a,boardsize) for a in ind_actions]
        eprint(ind_actions_cd[:10])
        # play the move

        for a in ind_actions:
            # THERE ARE NO PASS MOVES IN CNN
            # if a == N * N:  # pass move
            # mov = None
            # break
            mov = utils.a2p(a, N)

            if self.board.ko and mov == self.board.ko:  # move is a ko so continue
                continue
            #elif self.board.is_my_eye(c,mov):
               #eprint('it is my own eye, so dont play here. color:{} mov:{}'.format(c,utils.p2cd(mov,N)))
                #continue
            else:
                res = self.board.play(c, mov)
                if res < 0:
                    # error, so try next action
                    eprint('Illegal move. res:{} color:{} move:{}. we will try the next one'.format(res,c,mov))
                    continue
                else:
                    break
        else:
            #if there are no legal moves, then pass
            eprint('No legal moves. PASSING')
            mov = None

        return mov

def test_player(N, num_moves=10, verbose=False):
    player = CNNPlayer(N)
    for i in range(num_moves):
        if i % 2 == 0:
            player.genmove(Color.BLACK)
        else:
            player.genmove(Color.WHITE)
        if verbose:
            eprint(player.board)

    eprint(player.board)

def test_not_fill_eyes(N, num_moves=10, verbose=False):
    player = CNNPlayer(N)
    for i in range(num_moves):
        player.genmove(Color.BLACK)
        if verbose:
            eprint(player.board)
    eprint(player.board)

def test_kill(N=9):
    player = CNNPlayer(N)
    seq=['B D3', 'B D5', 'B C4', 'W D4']
    player.board.play_seq(seq)
    eprint(player.board)
    player.genmove(Color.BLACK)
    eprint(player.board)

def test_two_eyes(N=9):
    player = CNNPlayer(N)
    seq = ['B F9', 'B F8', 'B G7', 'B H6', 'B J6', 'B F7',
           'W G8', 'W H9', 'W H7', 'W J8', 'W G9']
    player.board.play_seq(seq)
    eprint(player.board)
    player.genmove(Color.WHITE)
    eprint(player.board)


def main():

    #test_player(9, num_moves=100, verbose=True)
    test_player(19, num_moves=361, verbose=True)
    #test_not_fill_eyes(19, num_moves=100, verbose=True)
    #test_kill(9)
    #test_two_eyes(9)


if __name__ == '__main__':
    main()