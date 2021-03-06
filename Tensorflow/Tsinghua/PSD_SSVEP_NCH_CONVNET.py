# MUSA MAHMOOD - Copyright 2017
# Python 3.6.1
# TF 1.4.1

# IMPORTS:
import tensorflow as tf
import os.path as path
import pandas as pd
import numpy as np
import os as os
import datetime
import glob
import time

from scipy.io import loadmat
from sklearn.model_selection import train_test_split
from tensorflow.python.tools import freeze_graph
from tensorflow.python.tools import optimize_for_inference_lib

# CONSTANTS:
TIMESTAMP_START = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H.%M.%S')
VERSION_NUMBER = 'v0.1.2'
DESCRIPTION_TRAINING_DATA = '_LAST32CHS_'
TRAINING_FOLDER_PATH = r'ssvep_benchmark/psd_200p/S1'
TEST_FOLDER_PATH = r'ssvep_benchmark/psd_200p/S1val'
EXPORT_DIRECTORY = 'model_exports/' + VERSION_NUMBER + '/'
KEY_X_DATA_DICTIONARY = 'relevant_data'
KEY_Y_DATA_DICTIONARY = 'Y'

# IMAGE SHAPE/CHARACTERISTICS
NUMBER_CLASSES = 5
TOTAL_DATA_CHANNELS = 64
DATA_WINDOW_SIZE = 200  # TODO: Make sure this is correct.
# SELECT_DATA_CHANNELS = np.asarray(range(0, 32))  # - 1
SELECT_DATA_CHANNELS = np.asarray(range(32, 64))  # - 1
NUMBER_DATA_CHANNELS = SELECT_DATA_CHANNELS.shape[0]  # Selects first int in shape
DEFAULT_IMAGE_SHAPE = [DATA_WINDOW_SIZE, NUMBER_DATA_CHANNELS]
INPUT_IMAGE_SHAPE = [1, DATA_WINDOW_SIZE, NUMBER_DATA_CHANNELS]

# MODEL CKPT SAVES:
MODEL_NAME = 'ssvep_net_' + str(NUMBER_DATA_CHANNELS) + 'ch'
CHECKPOINT_FILE = EXPORT_DIRECTORY + MODEL_NAME + '.ckpt'

# FOR MODEL DESIGN
if NUMBER_DATA_CHANNELS > 16:
    NUMBER_STEPS = 5000
else:
    NUMBER_STEPS = 10000

TRAIN_BATCH_SIZE = 64
TEST_BATCH_SIZE = 32
LEARNING_RATE = 1e-5  # 'Step size' on n-D optimization plane
STRIDE_CONV2D = [1, 1, 1, 1]
MAX_POOL_K_SIZE = [1, 2, 1, 1]
MAX_POOL_STRIDE = [1, 2, 1, 1]

BIAS_VAR_CL1 = 32
BIAS_VAR_CL2 = 64

if NUMBER_DATA_CHANNELS > 2:
    DIVIDER = 2
else:
    DIVIDER = 1

WEIGHT_VAR_CL1 = [NUMBER_CLASSES, NUMBER_DATA_CHANNELS, 1, BIAS_VAR_CL1]
WEIGHT_VAR_CL2 = [NUMBER_CLASSES, NUMBER_DATA_CHANNELS, BIAS_VAR_CL1, BIAS_VAR_CL2]

MAX_POOL_FLAT_SHAPE_FC1 = [-1, BIAS_VAR_CL1 * NUMBER_DATA_CHANNELS * (DATA_WINDOW_SIZE // DIVIDER)]

WEIGHT_VAR_FC1 = [(DATA_WINDOW_SIZE // DIVIDER) * NUMBER_DATA_CHANNELS * BIAS_VAR_CL1, BIAS_VAR_CL1 ** 2]

BIAS_VAR_FC1 = [(BIAS_VAR_CL1 ** 2)]
WEIGHT_VAR_FC_OUTPUT = [*BIAS_VAR_FC1, NUMBER_CLASSES]

BIAS_VAR_FC_OUTPUT = [NUMBER_CLASSES]

# Start Script Here:
output_folder_name = 'exports'
if not path.exists(output_folder_name):
    os.mkdir(output_folder_name)
input_node_name = 'input'
keep_prob_node_name = 'keep_prob'
output_node_name = 'output'


def load_data(data_directory):
    # x_train_data = np.empty([0, *[NUMBER_DATA_CHANNELS, DATA_WINDOW_SIZE]], np.float32)
    x_train_data = np.empty([0, *[DATA_WINDOW_SIZE, NUMBER_DATA_CHANNELS]], np.float32)
    y_train_data = np.empty([0], np.float32)
    training_files = glob.glob(data_directory + "/*.mat")
    for f in training_files:
        x_array_original = loadmat(f).get(KEY_X_DATA_DICTIONARY)
        x_array = x_array_original[:, SELECT_DATA_CHANNELS, :]
        # TODO: TEMP LINE:
        x_array = np.reshape(x_array, [x_array.shape[0], DATA_WINDOW_SIZE, NUMBER_DATA_CHANNELS])
        y_array = loadmat(f).get(KEY_Y_DATA_DICTIONARY)
        y_array = y_array.reshape([np.amax(y_array.shape)])
        x_train_data = np.concatenate((x_train_data, x_array), axis=0)
        y_train_data = np.concatenate((y_train_data, y_array), axis=0)
    y_train_data = np.asarray(pd.get_dummies(y_train_data).values).astype(np.float32)
    # return data_array
    print("Loaded Data Shape: X:", x_train_data.shape, " Y: ", y_train_data.shape)
    return x_train_data, y_train_data


def export_model(input_node_names, output_node_name_internal):
    freeze_graph.freeze_graph(EXPORT_DIRECTORY + MODEL_NAME + '.pbtxt', None, False,
                              EXPORT_DIRECTORY + MODEL_NAME + '.ckpt', output_node_name_internal, "save/restore_all",
                              "save/Const:0", EXPORT_DIRECTORY + '/frozen_' + MODEL_NAME + '.pb', True, "")
    input_graph_def = tf.GraphDef()
    with tf.gfile.Open(EXPORT_DIRECTORY + '/frozen_' + MODEL_NAME + '.pb', "rb") as f:
        input_graph_def.ParseFromString(f.read())
    output_graph_def = optimize_for_inference_lib.optimize_for_inference(
        input_graph_def, input_node_names, [output_node_name_internal], tf.float32.as_datatype_enum)
    with tf.gfile.FastGFile(EXPORT_DIRECTORY + '/opt_' + MODEL_NAME + '.pb', "wb") as f:
        f.write(output_graph_def.SerializeToString())

    print("Graph Saved - Output Directories: ")
    print("1 - Standard Frozen Model:", EXPORT_DIRECTORY + '/frozen_' + MODEL_NAME + '.pb')
    print("2 - Android Optimized Model:", EXPORT_DIRECTORY + '/opt_' + MODEL_NAME + '.pb')


# Model Building Macros: #
def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)


def bias_variable(shape):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)


# Convolution and max-pooling functions
def conv2d(x_, weights_):
    return tf.nn.conv2d(x_, weights_, strides=STRIDE_CONV2D, padding='SAME')


def max_pool_2x2(x_):
    return tf.nn.max_pool(x_, ksize=MAX_POOL_K_SIZE,
                          strides=MAX_POOL_STRIDE, padding='SAME')


def get_activations(layer, input_val, shape, directory, file_name, sum_all=False):
    os.makedirs(directory)
    units = sess.run(layer, feed_dict={x: np.reshape(input_val, shape, order='F'), keep_prob: 1.0})
    print("units.shape: ", units.shape)
    new_shape = [units.shape[1], units.shape[2]]
    feature_maps = units.shape[3]
    filename_ = directory + file_name
    if sum_all:
        new_array = np.reshape(units.sum(axis=3), new_shape)
        pd.DataFrame(new_array).to_csv(filename_ + '_weight_matrix' + '.csv', index=False, header=False)
        major_axis = np.argmax(new_array.shape)
        summed_array = new_array.sum(axis=major_axis)
        pd.DataFrame(summed_array).to_csv(filename_ + '_sum_all' + '.csv', index=False, header=False)
        print('All Values:')
        return summed_array
    else:
        for i0 in range(feature_maps):
            pd.DataFrame(units[:, :, :, i0].reshape(new_shape)).to_csv(
                filename_ + '_' + str(i0 + 1) + '.csv', index=False, header=False)
        return units


# MODEL INPUT #
x = tf.placeholder(tf.float32, shape=[None, *DEFAULT_IMAGE_SHAPE], name=input_node_name)
keep_prob = tf.placeholder(tf.float32, name=keep_prob_node_name)
y = tf.placeholder(tf.float32, shape=[None, NUMBER_CLASSES])

x_input = tf.reshape(x, [-1, *DEFAULT_IMAGE_SHAPE, 1])

# first convolution and pooling
W_conv1 = weight_variable(WEIGHT_VAR_CL1)
b_conv1 = bias_variable([BIAS_VAR_CL1])

h_conv1 = tf.nn.relu(conv2d(x_input, W_conv1) + b_conv1)
h_pool1 = max_pool_2x2(h_conv1)

# second convolution and pooling
W_conv2 = weight_variable(WEIGHT_VAR_CL2)
b_conv2 = bias_variable([BIAS_VAR_CL2])

h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)
h_pool2 = max_pool_2x2(h_conv2)

# the input should be shaped/flattened
h_pool2_flat = tf.reshape(h_pool2, MAX_POOL_FLAT_SHAPE_FC1)

# fully connected layer1,the shape of the patch should be defined
W_fc1 = weight_variable(WEIGHT_VAR_FC1)
b_fc1 = bias_variable(BIAS_VAR_FC1)

h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

h_fc2_drop = tf.nn.dropout(h_fc1, keep_prob)

# weight and bias of the output layer
W_fco = weight_variable(WEIGHT_VAR_FC_OUTPUT)
b_fco = bias_variable(BIAS_VAR_FC_OUTPUT)

y_conv = tf.matmul(h_fc2_drop, W_fco) + b_fco
outputs = tf.nn.softmax(y_conv, name=output_node_name)

# training and reducing the cost/loss function
cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=y, logits=y_conv))
train_step = tf.train.AdamOptimizer(LEARNING_RATE).minimize(cross_entropy)
correct_prediction = tf.equal(tf.argmax(outputs, 1), tf.argmax(y, 1))

accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

merged_summary_op = tf.summary.merge_all()

saver = tf.train.Saver()  # Initialize tf Saver

# Load Data:
x_data, y_data = load_data(TRAINING_FOLDER_PATH)
# x_val_data, y_val_data = load_data(TEST_FOLDER_PATH)
# Split training set:
x_train, x_test0, y_train, y_test0 = train_test_split(x_data, y_data, train_size=0.75, random_state=1)
x_test, x_val_data, y_test, y_val_data = train_test_split(x_test0, y_test0, train_size=0.50, random_state=1)

print("samples: train batch: ", x_train.shape)
print("samples: test batch: ", x_test.shape)
print("samples: validation batch: ", x_val_data.shape)

# TRAIN ROUTINE #
init_op = tf.global_variables_initializer()
config = tf.ConfigProto()
config.gpu_options.allow_growth = True

val_step = 0
with tf.Session(config=config) as sess:
    sess.run(init_op)
    # NOTE Restore old model if available
    if os.path.isfile(EXPORT_DIRECTORY + MODEL_NAME + '.ckpt'):
        saver.restore(sess, EXPORT_DIRECTORY + MODEL_NAME + '.ckpt')

    x_0 = np.zeros(INPUT_IMAGE_SHAPE, dtype=np.float32)
    print("Model Dimensions: ")
    print("h_conv1: ", sess.run(h_conv1, feed_dict={x: x_0, keep_prob: 1.0}).shape)
    print("h_pool1: ", sess.run(h_pool1, feed_dict={x: x_0, keep_prob: 1.0}).shape)
    print("h_conv2: ", sess.run(h_conv2, feed_dict={x: x_0, keep_prob: 1.0}).shape)
    print("h_pool2: ", sess.run(h_pool2, feed_dict={x: x_0, keep_prob: 1.0}).shape)
    print("h_pool2_flat: ", sess.run(h_pool2_flat, feed_dict={x: x_0, keep_prob: 1.0}).shape)
    print("h_fc1: ", sess.run(h_fc1, feed_dict={x: x_0, keep_prob: 1.0}).shape)
    print("h_fc1_drop: ", sess.run(h_fc2_drop, feed_dict={x: x_0, keep_prob: 1.0}).shape)
    print("y_conv: ", sess.run(y_conv, feed_dict={x: x_0, keep_prob: 1.0}).shape)

    # save model as pbtxt:
    tf.train.write_graph(sess.graph_def, EXPORT_DIRECTORY, MODEL_NAME + '.pbtxt', True)

    for i in range(NUMBER_STEPS):
        offset = (i * TRAIN_BATCH_SIZE) % (x_train.shape[0] - TRAIN_BATCH_SIZE)
        batch_x_train = x_train[offset:(offset + TRAIN_BATCH_SIZE)]
        batch_y_train = y_train[offset:(offset + TRAIN_BATCH_SIZE)]
        if i % 10 == 0:
            train_accuracy = accuracy.eval(feed_dict={x: batch_x_train, y: batch_y_train, keep_prob: 1.0})
            print("step %d, training accuracy %g" % (i, train_accuracy))

        if i % 20 == 0:
            # Calculate batch loss and accuracy
            offset = (val_step * TEST_BATCH_SIZE) % (x_test.shape[0] - TEST_BATCH_SIZE)
            batch_x_val = x_test[offset:(offset + TEST_BATCH_SIZE), :, :]
            batch_y_val = y_test[offset:(offset + TEST_BATCH_SIZE), :]
            val_accuracy = accuracy.eval(feed_dict={x: batch_x_val, y: batch_y_val, keep_prob: 1.0})
            print("Validation step %d, validation accuracy %g" % (val_step, val_accuracy))
            val_step += 1

        train_step.run(feed_dict={x: batch_x_train, y: batch_y_train, keep_prob: 0.25})

    # Run test data (entire set) to see accuracy.
    test_accuracy = sess.run(accuracy, feed_dict={x: x_test, y: y_test, keep_prob: 1.0})  # original
    print("\n Testing Accuracy:", test_accuracy, "\n\n")

    # Holdout Validation Accuracy:
    holdout_accuracy = sess.run(accuracy, feed_dict={x: x_val_data[0:128], y: y_val_data[0:128], keep_prob: 1.0})
    print("Holdout Validation:", holdout_accuracy, "\n\n")

    # Get one sample and see what it outputs (Activations?) ?
    image_output_folder_name = EXPORT_DIRECTORY + DESCRIPTION_TRAINING_DATA + TIMESTAMP_START + '/' + 'h_conv1/'
    filename = 'sum_h_conv1'
    # TODO: try with one (or multiple) samples from each class and average
    weights = get_activations(h_conv1, x_val_data[1, :, :], INPUT_IMAGE_SHAPE, image_output_folder_name,
                              filename, sum_all=True)
    print('weights', weights)
    # Read from the tail of the arg-sort to find the n highest elements:
    weights_sorted = np.argsort(weights)[::-1]  # [:2] select last 2
    print('weights_sorted: ', weights_sorted)
    if NUMBER_DATA_CHANNELS > 8:
        top_8_channel_select = np.sort(np.argsort(weights)[::-1][:8])
        print('Top 8 ch: ', top_8_channel_select)
    if NUMBER_DATA_CHANNELS > 4:
        top_4_channel_select = np.sort(np.argsort(weights)[::-1][:4])
        print('Top 4 ch: ', top_4_channel_select)
    top_2_channel_select = np.sort(np.argsort(weights)[::-1][:2])
    print('Top 2 ch: ', top_2_channel_select)

    user_input = input('Export Current Model?')
    if user_input == "1" or user_input.lower() == "y":
        saver.save(sess, CHECKPOINT_FILE)
        export_model([input_node_name, keep_prob_node_name], output_node_name)
