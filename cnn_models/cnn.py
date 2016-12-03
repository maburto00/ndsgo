# Copyright 2015 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Builds the CIFAR-10 network.

Summary of available functions:

 # Compute input images and labels for training. If you would like to run
 # evaluations, use inputs() instead.
 inputs, labels = distorted_inputs()

 # Compute inference on the model inputs to make a prediction.
 predictions = inference(inputs)

 # Compute the total loss of the prediction with respect to the labels.
 loss = loss(predictions, labels)

 # Create a graph to run one step of training with respect to the loss.
 train_op = train(loss, global_step)
"""
# pylint: disable=missing-docstring
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import gzip
import os
import re
import sys
import tarfile

from six.moves import urllib
import tensorflow as tf

# from tensorflow.models.image.cifar10 import cifar10_input
from cnn_models import cnn_input

FLAGS = tf.app.flags.FLAGS

# Basic model parameters.
tf.app.flags.DEFINE_integer('batch_size', 16,
                            """Number of images to process in a batch.""")
tf.app.flags.DEFINE_string('data_dir', '/home/mario/datasets/gogod_9x9_games_dataset',
                           """Path to the data directory.""")
#tf.app.flags.DEFINE_string('data_dir', 'KGS_10games',
#                           """Path to the data directory.""")

tf.app.flags.DEFINE_boolean('use_fp16', False,
                            """Train the model using fp16.""")

# Global constants describing the CIFAR-10 data set.
# TODO: all of this should be defined in FLAGS
#IMAGE_SIZE = cnn_input.IMAGE_SIZE
#NUM_CLASSES = cnn_input.NUM_CLASSES
#NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN = cnn_input.NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN
#NUM_EXAMPLES_PER_EPOCH_FOR_EVAL = cnn_input.NUM_EXAMPLES_PER_EPOCH_FOR_EVAL
NUM_FILTERS=32

# Constants describing the training process.
MOVING_AVERAGE_DECAY = 0.9999  # The decay to use for the moving average.
#NUM_EPOCHS_PER_DECAY = 350.0  # Epochs after which learning rate decays.
DECAY_STEPS=30000
LEARNING_RATE_DECAY_FACTOR = 0.1  # Learning rate decay factor.
INITIAL_LEARNING_RATE = 0.1  # Initial learning rate.

# If a model is trained with multiple GPUs, prefix all Op names with tower_name
# to differentiate the operations. Note that this prefix is removed from the
# names of the summaries when visualizing a model.
TOWER_NAME = 'tower'


def _activation_summary(x):
    """Helper to create summaries for activations.

    Creates a summary that provides a histogram of activations.
    Creates a summary that measures the sparsity of activations.

    Args:
      x: Tensor
    Returns:
      nothing
    """
    # Remove 'tower_[0-9]/' from the name in case this is a multi-GPU training
    # session. This helps the clarity of presentation on tensorboard.
    tensor_name = re.sub('%s_[0-9]*/' % TOWER_NAME, '', x.op.name)
    tf.histogram_summary(tensor_name + '/activations', x)
    tf.scalar_summary(tensor_name + '/sparsity', tf.nn.zero_fraction(x))


def _variable_on_cpu(name, shape, initializer):
    """Helper to create a Variable stored on CPU memory.

    Args:
      name: name of the variable
      shape: list of ints
      initializer: initializer for Variable

    Returns:
      Variable Tensor
    """
    with tf.device('/cpu:0'):
        dtype = tf.float16 if FLAGS.use_fp16 else tf.float32
        var = tf.get_variable(name, shape, initializer=initializer, dtype=dtype)
    return var


def _variable_with_weight_decay(name, shape, stddev, wd):
    """Helper to create an initialized Variable with weight decay.

    Note that the Variable is initialized with a truncated normal distribution.
    A weight decay is added only if one is specified.

    Args:
      name: name of the variable
      shape: list of ints
      stddev: standard deviation of a truncated Gaussian
      wd: add L2Loss weight decay multiplied by this float. If None, weight
          decay is not added for this Variable.

    Returns:
      Variable Tensor
    """
    dtype = tf.float16 if FLAGS.use_fp16 else tf.float32
    var = _variable_on_cpu(
        name,
        shape,
        tf.truncated_normal_initializer(stddev=stddev, dtype=dtype))
    if wd is not None:
        weight_decay = tf.mul(tf.nn.l2_loss(var), wd, name='weight_loss')
        tf.add_to_collection('losses', weight_decay)
    return var


def distorted_inputs(num_train_files,train_num_examples,boardsize,num_channels):
    """Construct distorted input for CIFAR training using the Reader ops.

    Returns:
      images: Images. 4D tensor of [batch_size, IMAGE_SIZE, IMAGE_SIZE, 3] size.
      labels: Labels. 1D tensor of [batch_size] size.

    Raises:
      ValueError: If no data_dir
    """
    if not FLAGS.data_dir:
        raise ValueError('Please supply a data_dir')
    data_dir = FLAGS.data_dir
    images, labels = cnn_input.distorted_inputs(data_dir=data_dir,
                                                batch_size=FLAGS.batch_size,
                                                num_train_files=num_train_files,
                                                train_num_examples=train_num_examples,
                                                boardsize=boardsize,
                                                num_channels=num_channels)
    if FLAGS.use_fp16:
        images = tf.cast(images, tf.float16)
        labels = tf.cast(labels, tf.float16)
    return images, labels


def inputs(eval_data,num_train_files,train_num_examples,test_num_examples, boardsize,num_channels):
    """Construct input for CIFAR evaluation using the Reader ops.

    Args:
      eval_data: bool, indicating if one should use the train or eval data set.

    Returns:
      images: Images. 4D tensor of [batch_size, IMAGE_SIZE, IMAGE_SIZE, 3] size.
      labels: Labels. 1D tensor of [batch_size] size.

    Raises:
      ValueError: If no data_dir
    """
    if not FLAGS.data_dir:
        raise ValueError('Please supply a data_dir')
    data_dir = FLAGS.data_dir
    images, labels = cnn_input.inputs(eval_data=eval_data,
                                      data_dir=data_dir,
                                      batch_size=FLAGS.batch_size,
                                      num_train_files=num_train_files,
                                      train_num_examples=train_num_examples,
                                      test_num_examples=test_num_examples,
                                      boardsize=boardsize,
                                      num_channels=num_channels)
    if FLAGS.use_fp16:
        images = tf.cast(images, tf.float16)
        labels = tf.cast(labels, tf.float16)
    return images, labels

def inference_layer(images,boardsize,num_channels,intermediate_layers=1):
    """Build the model.

    Args:
      images: Images returned from distorted_inputs() or inputs().

    Returns:
      Logits.
    """
    # We instantiate all variables using tf.get_variable() instead of
    # tf.Variable() in order to share variables across multiple GPU training runs.
    # If we only ran this model on a single GPU, we could simplify this function
    # by replacing all instances of tf.get_variable() with tf.Variable().
    #
    # conv1
    with tf.variable_scope('conv1') as scope:
        kernel = _variable_with_weight_decay('weights',
                                             shape=[5, 5, num_channels, NUM_FILTERS],
                                             stddev=0.1,
                                             wd=0.0)
        conv = tf.nn.conv2d(images, kernel, [1, 1, 1, 1], padding='SAME')
        biases = _variable_on_cpu('biases', [NUM_FILTERS], tf.constant_initializer(0.0))
        bias = tf.nn.bias_add(conv, biases)
        conv_relu= tf.nn.relu(bias, name=scope.name)
        _activation_summary(conv_relu)

    #conv_relu=conv1
    for i in range(intermediate_layers):
        with tf.variable_scope('conv{}'.format(i+2)) as scope:
            kernel = _variable_with_weight_decay('weights',
                                                 shape=[3, 3, NUM_FILTERS, NUM_FILTERS],
                                                 stddev=0.1,
                                                 wd=0.0)
            conv = tf.nn.conv2d(conv_relu, kernel, [1, 1, 1, 1], padding='SAME')
            biases = _variable_on_cpu('biases', [NUM_FILTERS], tf.constant_initializer(0.0))
            bias = tf.nn.bias_add(conv, biases)
            conv_relu = tf.nn.relu(bias, name=scope.name)
            _activation_summary(conv_relu)

    # conv2
    # softmax, i.e. softmax(WX + b)
    with tf.variable_scope('conv_last') as scope:
        kernel = _variable_with_weight_decay('weights',
                                             shape=[1, 1, NUM_FILTERS, 1],
                                             stddev=0.1,
                                             wd=0.0)
        conv = tf.nn.conv2d(conv_relu, kernel, [1, 1, 1, 1], padding='SAME')
        conv_shape = conv.get_shape().as_list()
        reshape = tf.reshape(conv,[conv_shape[0], conv_shape[1] * conv_shape[2] * conv_shape[3]])

        biases = _variable_on_cpu('biases', [boardsize*boardsize],
                                  tf.constant_initializer(0.1))

        logits= tf.nn.relu(reshape + biases ,name=scope.name)


        #reshape = tf.reshape(conv2, [FLAGS.batch_size,-1])
        #weights = _variable_with_weight_decay('weights', [192, boardsize*boardsize],
        #                                      stddev=1 / 192.0, wd=0.0)
        #biases = _variable_on_cpu('biases', [boardsize*boardsize],
        #                          tf.constant_initializer(0.0))
        #_activation_summary(softmax_linear)

    return logits

def inference_l2(images,boardsize,num_channels):
    """Build the model.

    Args:
      images: Images returned from distorted_inputs() or inputs().

    Returns:
      Logits.
    """
    # We instantiate all variables using tf.get_variable() instead of
    # tf.Variable() in order to share variables across multiple GPU training runs.
    # If we only ran this model on a single GPU, we could simplify this function
    # by replacing all instances of tf.get_variable() with tf.Variable().
    #
    # conv1
    with tf.variable_scope('conv1') as scope:
        kernel = _variable_with_weight_decay('weights',
                                             shape=[5, 5, num_channels, NUM_FILTERS],
                                             stddev=0.1,
                                             wd=0.0)
        conv = tf.nn.conv2d(images, kernel, [1, 1, 1, 1], padding='SAME')
        biases = _variable_on_cpu('biases', [NUM_FILTERS], tf.constant_initializer(0.0))
        bias = tf.nn.bias_add(conv, biases)
        conv1 = tf.nn.relu(bias, name=scope.name)
        _activation_summary(conv1)

    with tf.variable_scope('conv2') as scope:
        kernel = _variable_with_weight_decay('weights',
                                             shape=[3, 3, NUM_FILTERS, NUM_FILTERS],
                                             stddev=0.1,
                                             wd=0.0)
        conv = tf.nn.conv2d(conv1, kernel, [1, 1, 1, 1], padding='SAME')
        biases = _variable_on_cpu('biases', [NUM_FILTERS], tf.constant_initializer(0.0))
        bias = tf.nn.bias_add(conv, biases)
        conv2 = tf.nn.relu(bias, name=scope.name)
        _activation_summary(conv2)

    # conv2
    # softmax, i.e. softmax(WX + b)
    with tf.variable_scope('logits') as scope:
        kernel = _variable_with_weight_decay('weights',
                                             shape=[1, 1, NUM_FILTERS, 1],
                                             stddev=0.1,
                                             wd=0.0)
        conv = tf.nn.conv2d(conv2, kernel, [1, 1, 1, 1], padding='SAME')
        conv_shape = conv.get_shape().as_list()
        reshape = tf.reshape(conv,[conv_shape[0], conv_shape[1] * conv_shape[2] * conv_shape[3]])

        biases = _variable_on_cpu('biases', [boardsize*boardsize],
                                  tf.constant_initializer(0.1))

        logits= tf.nn.relu(reshape + biases ,name=scope.name)


        #reshape = tf.reshape(conv2, [FLAGS.batch_size,-1])
        #weights = _variable_with_weight_decay('weights', [192, boardsize*boardsize],
        #                                      stddev=1 / 192.0, wd=0.0)
        #biases = _variable_on_cpu('biases', [boardsize*boardsize],
        #                          tf.constant_initializer(0.0))
        #_activation_summary(softmax_linear)

    return logits


def inference(images,boardsize,num_channels):
    """Build the model.

    Args:
      images: Images returned from distorted_inputs() or inputs().

    Returns:
      Logits.
    """
    # We instantiate all variables using tf.get_variable() instead of
    # tf.Variable() in order to share variables across multiple GPU training runs.
    # If we only ran this model on a single GPU, we could simplify this function
    # by replacing all instances of tf.get_variable() with tf.Variable().
    #
    # conv1
    with tf.variable_scope('conv1') as scope:
        kernel = _variable_with_weight_decay('weights',
                                             shape=[5, 5, num_channels, 32],
                                             stddev=0.1,
                                             wd=0.0)
        conv = tf.nn.conv2d(images, kernel, [1, 1, 1, 1], padding='SAME')
        biases = _variable_on_cpu('biases', [32], tf.constant_initializer(0.0))
        bias = tf.nn.bias_add(conv, biases)
        conv1 = tf.nn.relu(bias, name=scope.name)
        _activation_summary(conv1)

    # pool1
    #pool1 = tf.nn.max_pool(conv1, ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1],
     #                      padding='SAME', name='pool1')
    # norm1
    #norm1 = tf.nn.lrn(pool1, 4, bias=1.0, alpha=0.001 / 9.0, beta=0.75,
#                      name='norm1')

    # conv2
    # softmax, i.e. softmax(WX + b)
    with tf.variable_scope('logits') as scope:
        kernel = _variable_with_weight_decay('weights',
                                             shape=[1, 1, 32, 1],
                                             stddev=0.1,
                                             wd=0.0)
        conv = tf.nn.conv2d(conv1, kernel, [1, 1, 1, 1], padding='SAME')
        conv_shape = conv.get_shape().as_list()
        reshape = tf.reshape(conv,[conv_shape[0], conv_shape[1] * conv_shape[2] * conv_shape[3]])

        biases = _variable_on_cpu('biases', [boardsize*boardsize],
                                  tf.constant_initializer(0.1))

        logits= tf.nn.relu(reshape + biases ,name=scope.name)


        #reshape = tf.reshape(conv2, [FLAGS.batch_size,-1])
        #weights = _variable_with_weight_decay('weights', [192, boardsize*boardsize],
        #                                      stddev=1 / 192.0, wd=0.0)
        #biases = _variable_on_cpu('biases', [boardsize*boardsize],
        #                          tf.constant_initializer(0.0))
        #_activation_summary(softmax_linear)

    return logits


def loss(logits, labels):
    """Add L2Loss to all the trainable variables.

    Add summary for "Loss" and "Loss/avg".
    Args:
      logits: Logits from inference().
      labels: Labels from distorted_inputs or inputs(). 1-D tensor
              of shape [batch_size]

    Returns:
      Loss tensor of type float.
    """
    # Calculate the average cross entropy loss across the batch.

    labels = tf.cast(labels, tf.int64)
    cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(
        logits, labels, name='cross_entropy_per_example')
    cross_entropy_mean = tf.reduce_mean(cross_entropy, name='cross_entropy')
    tf.add_to_collection('losses', cross_entropy_mean)

    # The total loss is defined as the cross entropy loss plus all of the weight
    # decay terms (L2 loss).
    return tf.add_n(tf.get_collection('losses'), name='total_loss')


def _add_loss_summaries(total_loss):
    """Add summaries for losses in CIFAR-10 model.

    Generates moving average for all losses and associated summaries for
    visualizing the performance of the network.

    Args:
      total_loss: Total loss from loss().
    Returns:
      loss_averages_op: op for generating moving averages of losses.
    """
    # Compute the moving average of all individual losses and the total loss.
    loss_averages = tf.train.ExponentialMovingAverage(0.9, name='avg')
    losses = tf.get_collection('losses')
    loss_averages_op = loss_averages.apply(losses + [total_loss])

    # Attach a scalar summary to all individual losses and the total loss; do the
    # same for the averaged version of the losses.
    for l in losses + [total_loss]:
        # Name each loss as '(raw)' and name the moving average version of the loss
        # as the original loss name.
        tf.scalar_summary(l.op.name + ' (raw)', l)
        tf.scalar_summary(l.op.name, loss_averages.average(l))

    return loss_averages_op


def train(total_loss, global_step,train_num_examples):
    """Train CIFAR-10 model.

    Create an optimizer and apply to all trainable variables. Add moving
    average for all trainable variables.

    Args:
      total_loss: Total loss from loss().
      global_step: Integer Variable counting the number of training steps
        processed.
    Returns:
      train_op: op for training.
    """
    # Variables that affect learning rate.
    #num_batches_per_epoch = train_num_examples / FLAGS.batch_size
    #decay_steps = int(num_batches_per_epoch * NUM_EPOCHS_PER_DECAY)
    decay_steps=DECAY_STEPS

    # Decay the learning rate exponentially based on the number of steps.
    lr = tf.train.exponential_decay(INITIAL_LEARNING_RATE,
                                    global_step,
                                    decay_steps,
                                    LEARNING_RATE_DECAY_FACTOR,
                                    staircase=True)
    tf.scalar_summary('learning_rate', lr)

    # Generate moving averages of all losses and associated summaries.
    loss_averages_op = _add_loss_summaries(total_loss)

    # Compute gradients.
    with tf.control_dependencies([loss_averages_op]):
        opt = tf.train.GradientDescentOptimizer(lr)
        grads = opt.compute_gradients(total_loss)

    # Apply gradients.
    apply_gradient_op = opt.apply_gradients(grads, global_step=global_step)

    # Add histograms for trainable variables.
    for var in tf.trainable_variables():
        tf.histogram_summary(var.op.name, var)

    # Add histograms for gradients.
    for grad, var in grads:
        if grad is not None:
            tf.histogram_summary(var.op.name + '/gradients', grad)

    # Track the moving averages of all trainable variables.
    variable_averages = tf.train.ExponentialMovingAverage(
        MOVING_AVERAGE_DECAY, global_step)
    variables_averages_op = variable_averages.apply(tf.trainable_variables())

    with tf.control_dependencies([apply_gradient_op, variables_averages_op]):
        train_op = tf.no_op(name='train')

    return train_op

def read_properties_file():

    for fn in os.listdir(FLAGS.data_dir):
        if fn.endswith('.prop'):
            property_fn=fn
            break

    with open(os.path.join(FLAGS.data_dir,property_fn),'r') as f:
        num_examples=[int(c) for c in f.readline().strip().split(',')]
        num_train_files=len(num_examples)-1
        train_num_examples=sum(num_examples[:-1])
        test_num_examples=int(num_examples[-1])
        num_channels=int(f.readline().strip())
        boardsize=int(f.readline().strip())

        print(num_examples,train_num_examples,test_num_examples,num_channels,boardsize)
    return num_train_files,train_num_examples,test_num_examples,num_channels,boardsize
