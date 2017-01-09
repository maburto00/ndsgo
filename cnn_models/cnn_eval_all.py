from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
import math
import time

import numpy as np
import tensorflow as tf
import os
from board import Board

from cnn_models import cnn

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_string('eval_dir', 'gogod_eval_l2_new',
                           """Directory where to write event logs.""")
tf.app.flags.DEFINE_string('eval_data', 'train_eval',
                           """Either 'test' or 'train_eval'.""")
tf.app.flags.DEFINE_string('checkpoint_dir', 'gogod_train_l2_new',
                           """Directory where to read model checkpoints.""")
tf.app.flags.DEFINE_integer('eval_interval_secs', 5,
                            """How often to run the eval.""")
#5760, 643
tf.app.flags.DEFINE_integer('num_examples', 5760,
                            """Number of examples to run.""")
tf.app.flags.DEFINE_boolean('run_once', False,
                            """Whether to run eval only once.""")


def eval_once(saver, summary_writer, top_k_op, summary_op,num_examples,file_name):
    """Run Eval once.

    Args:
      saver: Saver.
      summary_writer: Summary writer.
      top_k_op: Top K op.
      summary_op: Summary op.
    """
    with tf.Session() as sess:
        ckpt = tf.train.get_checkpoint_state(FLAGS.checkpoint_dir)
        if ckpt and ckpt.model_checkpoint_path:
            # Restores from checkpoint
            saver.restore(sess, file_name)
            # Assuming model_checkpoint_path looks something like:
            #   /my-favorite-path/train/model.ckpt-0,
            # extract global_step from it.
            global_step = ckpt.model_checkpoint_path.split('/')[-1].split('-')[-1]
            #print('global_step:{}'.format(global_step))
        else:
            print('No checkpoint file found')
            return

        # Start the queue runners.
        coord = tf.train.Coordinator()
        try:
            threads = []
            for qr in tf.get_collection(tf.GraphKeys.QUEUE_RUNNERS):
                threads.extend(qr.create_threads(sess, coord=coord, daemon=True,
                                                 start=True))

            #num_iter = int(math.ceil(num_examples / FLAGS.batch_size))

            num_iter = int(math.ceil(FLAGS.num_examples / FLAGS.batch_size))
            print('num_iter:{}'.format(num_iter))
            true_count = 0  # Counts the number of correct predictions.
            total_sample_count = num_iter * FLAGS.batch_size
            step = 0
            PRINT_INTERVAL = int(num_iter / 10)
            if PRINT_INTERVAL==0:
                PRINT_INTERVAL=1
            while step < num_iter and not coord.should_stop():
                predictions = sess.run([top_k_op])
                if step % PRINT_INTERVAL == 0 or step == num_iter:
                    print('step:{} num_iter:{}'.format(step,num_iter))
                #print(predictions)
                #board=Board(boardsize)
                #board.get_board_and_move_from_register_str(boardsize,)

                true_count += np.sum(predictions)
                step += 1

            # Compute precision @ 1.
            precision = true_count / total_sample_count
            print('%s: precision @ 1 = %.3f' % (datetime.now(), precision))

            summary = tf.Summary()
            summary.ParseFromString(sess.run(summary_op))
            summary.value.add(tag='Precision @ 1', simple_value=precision)
            summary_writer.add_summary(summary, global_step)
        except Exception as e:  # pylint: disable=broad-except
            coord.request_stop(e)

        coord.request_stop()
        coord.join(threads, stop_grace_period_secs=10)


def evaluate():
    """Eval for a number of steps."""
    with tf.Graph().as_default() as g:
        # Get images and labels
        eval_data = FLAGS.eval_data == 'test'
        images, labels = cnn.inputs(eval_data, num_train_files, train_num_examples, test_num_examples, boardsize, num_channels)

        # Build a Graph that computes the logits predictions from the
        # inference model.
        #logits = cnn.inference(images, boardsize, num_channels)
        logits = cnn.inference_layer(images, boardsize, num_channels,0)

        # Calculate predictions.
        top_k_op = tf.nn.in_top_k(logits, labels, 1)

        #print(top_k_op)
        #with tf.Session() as sess:
         #   sess.

        # Restore the moving average version of the learned variables for eval.
        variable_averages = tf.train.ExponentialMovingAverage(
            cnn.MOVING_AVERAGE_DECAY)
        variables_to_restore = variable_averages.variables_to_restore()
        saver = tf.train.Saver(variables_to_restore)

        # Build the summary operation based on the TF collection of Summaries.
        summary_op = tf.merge_all_summaries()

        summary_writer = tf.train.SummaryWriter(FLAGS.eval_dir, g)

        for step in range(0,21000,1000):
            dir_name = '/home/mario/Dropbox/PycharmProjects/ndsgo/cnn_models/{}'.format(FLAGS.checkpoint_dir)
            fn="model.ckpt-{}".format(step)
            full_fn= os.path.join(dir_name,fn)

            #print('dirname:{}'.format(dir_name))
            #print('fn:{}'.format(fn))
            print('full_fn:{}'.format(full_fn))
            print('global_step:{}'.format(step))
            eval_once(saver, summary_writer, top_k_op, summary_op,test_num_examples,full_fn)
            #eval_once(saver, summary_writer, top_k_op, summary_op, 1000)
            if FLAGS.run_once:
                break
            #time.sleep(FLAGS.eval_interval_secs)


def main(argv=None):  # pylint: disable=unused-argument
    if tf.gfile.Exists(FLAGS.eval_dir):
        tf.gfile.DeleteRecursively(FLAGS.eval_dir)
    tf.gfile.MakeDirs(FLAGS.eval_dir)

    global boardsize
    global num_channels
    global train_num_examples
    global test_num_examples
    global num_train_files
    num_train_files, train_num_examples, test_num_examples, num_channels, boardsize = cnn.read_properties_file()

    evaluate()


if __name__ == '__main__':
    tf.app.run()
