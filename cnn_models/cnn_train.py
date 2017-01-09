from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
import os.path
import time
from board import Board
from utils import Color
import utils
import numpy as np
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf

from cnn_models import cnn

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_string('train_dir', 'gogod_train_l2_new',
                           """Directory where to write event logs """
                           """and checkpoint.""")
tf.app.flags.DEFINE_integer('max_steps', 1000010,
                            """Number of batches to run.""")
tf.app.flags.DEFINE_boolean('log_device_placement', False,
                            """Whether to log device placement.""")

def train():
    """Train for a number of steps."""
    with tf.Graph().as_default():
        global_step = tf.Variable(0, trainable=False)

        # Get images and labels
        images, labels = cnn.distorted_inputs(num_train_files,train_num_examples,
                                                     boardsize,
                                                     num_channels)

        # Build a Graph that computes the logits predictions from the
        # inference model.
        #logits = cnn.inference_l2(images, boardsize, num_channels)
        #13->11, 3->1,2->0
        logits = cnn.inference_layer(images, boardsize, num_channels,0)
        #logits=cnn.inference(images,boardsize,num_channels)

        # Calculate loss.
        loss = cnn.loss(logits, labels)

        # Build a Graph that trains the model with one batch of examples and
        # updates the model parameters.
        train_op = cnn.train(loss, global_step, train_num_examples)

        # Create a saver.
        saver = tf.train.Saver(tf.all_variables(),max_to_keep=50)

        saver_exp= tf.train.Saver(tf.all_variables())

        # Build the summary operation based on the TF collection of Summaries.
        summary_op = tf.merge_all_summaries()

        # Build an initialization operation to run below.
        init = tf.initialize_all_variables()

        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)

        # Start running operations on the Graph.
        sess = tf.Session(config=tf.ConfigProto(
            log_device_placement=FLAGS.log_device_placement,gpu_options=gpu_options))
        sess.run(init)

        stored_performace=[]

        # Start the queue runners.
        tf.train.start_queue_runners(sess=sess)

        summary_writer = tf.train.SummaryWriter(FLAGS.train_dir, sess.graph)

        for step in xrange(FLAGS.max_steps):
            start_time = time.time()
            _, loss_value= sess.run([train_op, loss])
            #images = sess.run(images)
            duration = time.time() - start_time

            # np.set_printoptions(threshold="nan")
            # images=np.array(images)
            # images=images.transpose(0, 3, 1, 2)
            # image=images[0]
            # reg=bytearray([1,0])+bytearray(image.reshape([19*19*4]))
            # print(image)
            # board, a = Board.get_board_and_move_from_register_str(19,reg,Color.BLACK)
            # print(board)
            # p=utils.a2p(a,19)
            # cd=utils.p2cd(p,19)
            # print('a:{} p:{} cd:{}'.format(a,p,cd))
            #
            # print(images[0])

            assert not np.isnan(loss_value), 'Model diverged with loss = NaN'

            if step % 10 == 0:
                num_examples_per_step = FLAGS.batch_size
                examples_per_sec = num_examples_per_step / duration
                sec_per_batch = float(duration)

                format_str = ('%s: step %d, loss = %.2f (%.1f examples/sec; %.3f '
                              'sec/batch)')
                print(format_str % (datetime.now(), step, loss_value,
                                    examples_per_sec, sec_per_batch))

                #print(stored_performace)


            if step % 100 == 0:
                summary_str = sess.run(summary_op)
                summary_writer.add_summary(summary_str, step)

            # Save the model checkpoint periodically.
            if step % 1000 == 0 or (step + 1) == FLAGS.max_steps:
                checkpoint_path = os.path.join(FLAGS.train_dir, 'model.ckpt')
                saver.save(sess, checkpoint_path, global_step=step)

            if step==10 or step ==100 or step==1000 or step==10000 or step==100000 or step==1000000:
                checkpoint_path = os.path.join(FLAGS.train_dir, 'model_exp.ckpt')
                saver_exp.save(sess, checkpoint_path, global_step=step)

        #print(stored_performace)


def main(argv=None):  # pylint: disable=unused-argument

    if tf.gfile.Exists(FLAGS.train_dir):
        tf.gfile.DeleteRecursively(FLAGS.train_dir)
    tf.gfile.MakeDirs(FLAGS.train_dir)

    global boardsize
    global num_channels
    #NUM_CHANNELS=num_channels
    global train_num_examples
    #NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN=train_num_examples
    global test_num_examples
    #NUM_EXAMPLES_PER_EPOCH_FOR_EVAL=test_num_examples
    global num_train_files

    num_train_files,train_num_examples, test_num_examples, num_channels, boardsize=cnn.read_properties_file()

    train()


if __name__ == '__main__':
    tf.app.run()
