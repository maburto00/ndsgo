import tensorflow as tf
from cnn_models import cnn
from cnn_models import cnn_train
from board import Board
import utils
import struct
import numpy as np

def test_predict():
    with tf.Graph().as_default():

        boardsize=19
        num_channels=4

        board=Board(boardsize)
        #seq = ['b B3', 'b C4', 'b C2', 'B D3',
#               'W D4', 'w E3', 'w D2']
        seq=['b Q16']
        board.play_seq(seq)
        print(board)

        #move='Q16'
        # get input to the neural network
        c,p=utils.c_cd2cp(seq[0],boardsize)
        board_reg_str=str(board.create_board_register(utils.Color.WHITE,4))
        #data = data.reshape(num_images, NUM_CHANNELS, IMAGE_SIZE, IMAGE_SIZE)
        #data = data.transpose(0, 2, 3, 1)

        data = np.frombuffer(board_reg_str, dtype=np.uint8)
        data = data.astype(np.float32)
        data = data.reshape(1, num_channels, boardsize, boardsize)
        print(data)
        data = data.transpose(0, 2, 3, 1)
        print(data)

        # images=tf.placeholder(tf.float64,shape=[None,num_channels,boardsize,boardsize])
        logits = cnn.inference_layer(data,boardsize,num_channels,11)
        sm_output=tf.nn.softmax(logits)

        init = tf.initialize_all_variables()

        saver = tf.train.Saver()
        with tf.Session() as sess:
            # Restore variables from disk.
            saver.restore(sess, "KGS_train_l13/model.ckpt-12000")
            print("Model restored.")
            output=sess.run(sm_output)
            a = np.argmax(output)
            print(output,utils.p2cd(utils.a2p(a,boardsize),boardsize))
            #get top 5 prediction
            top_5=output[0].argsort()[::-1][:5]
            print(top_5)
            for e in top_5:
                print(utils.p2cd(utils.a2p(e,boardsize),boardsize))

            print(board)
            # Do some work with the model



def main():
    test_predict()
    #logits = cnn.inference(images, boardsize, num_channels)



if __name__=='__main__':
    main()