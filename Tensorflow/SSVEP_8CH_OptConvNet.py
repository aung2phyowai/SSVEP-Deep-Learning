# MUSA MAHMOOD - Copyright 2017
# Python 3.6.1
# TF 1.2.1

# IMPORTS:
import pandas as pd
import numpy as np
import tensorflow as tf
import os.path as path
import os as os
import glob
import itertools as it

from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from tensorflow.python.tools import freeze_graph
from tensorflow.python.tools import optimize_for_inference_lib

# CONSTANTS:
VERSION_NUMBER = 'v0.0.5'
TRAINING_FOLDER_PATH = r'_data/S1copy'
EXPORT_DIRECTORY = 'model_exports/' + VERSION_NUMBER + '/'
MODEL_NAME = 'ssvep_net_2ch'
NUMBER_STEPS = 5000
TRAIN_BATCH_SIZE = 256
VAL_BATCH_SIZE = 10
DATA_WINDOW_SIZE = 300
MOVING_WINDOW_SHIFT = 60
NUMBER_DATA_CHANNELS = 2


# METHODS:
def load_training_data():
    # Initialize array that will hold training data
    data_array = np.empty([0, 3], np.float64)

    training_files = glob.glob(TRAINING_FOLDER_PATH+"/*.csv")
    for f in training_files:
        data_from_file = pd.read_csv(f, header=None)  # read from file
        data_as_matrix = pd.DataFrame.as_matrix(data_from_file)  # convert to numpy array
        print("Size of file ", f, " is ",  data_as_matrix.shape)
        # If dimensionality matches, concatenate with data_array:
        if data_array.shape[1] == data_as_matrix.shape[1]:
            data_array = np.concatenate((data_array, data_as_matrix), axis=0)
    print("data_array final shape: \n", data_array.shape)
    return data_array


def moving_window(data, length, step):
    # Prepare windows of 'length'
    streams = it.tee(data, length)
    # Use step of step, but don't skip any (overlap)
    return zip(*[it.islice(stream, i, None, step) for stream, i in zip(streams, it.count(step=1))])


def model_input(input_node_name, keep_prob_node_name):
    x = tf.placeholder(tf.float32, shape=[None, DATA_WINDOW_SIZE*NUMBER_DATA_CHANNELS], name=input_node_name)
    keep_prob = tf.placeholder(tf.float32, name=keep_prob_node_name)
    y_ = tf.placeholder(tf.float32, shape=[None, 5])
    return x, keep_prob, y_


# weights and bias functions for convolution
def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)


def bias_variable(shape):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)


# Convolution and max-pooling functions
def conv2d(x, Weights):
    return tf.nn.conv2d(x, Weights, strides=[1, 1, 1, 1], padding='SAME')


def max_pool_2x2(x):
    return tf.nn.max_pool(x, ksize=[1, 2, 1, 1],
                          strides=[1, 2, 1, 1], padding='SAME')


def build_model(x, keep_prob, y, output_node_name):
    x_input = tf.reshape(x, [-1, DATA_WINDOW_SIZE, NUMBER_DATA_CHANNELS, 1])

    # first convolution and pooling
    W_conv1 = weight_variable([5, 1, 1, 32])
    b_conv1 = bias_variable([32])

    h_conv1 = tf.nn.relu(conv2d(x_input, W_conv1) + b_conv1)
    h_pool1 = max_pool_2x2(h_conv1)

    # second convolution and pooling
    W_conv2 = weight_variable([5, 1, 32, 64])
    b_conv2 = bias_variable([64])

    h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)
    h_pool2 = max_pool_2x2(h_conv2)

    # fully connected layer1,the shape of the patch should be defined
    W_fc1 = weight_variable([75 * 2 * 64, 1024])
    b_fc1 = bias_variable([1024])

    # the input should be shaped/flattened
    h_pool2_flat = tf.reshape(h_pool2, [-1, 75 * 2 * 64])
    h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

    # fully connected layer2
    W_fc2 = weight_variable([1024, 2048])
    b_fc2 = bias_variable([2048])
    h_fc2 = tf.nn.relu(tf.matmul(h_fc1, W_fc2) + b_fc2)

    h_fc2_drop = tf.nn.dropout(h_fc2, keep_prob)

    # weight and bias of the output layer
    W_fco = weight_variable([2048, 5])
    b_fco = bias_variable([5])

    y_conv = tf.matmul(h_fc2_drop, W_fco) + b_fco
    outputs = tf.nn.softmax(y_conv, name=output_node_name)

    # training and reducing the cost/loss function
    cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=y, logits=y_conv))
    train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)
    # correct_prediction = tf.equal(tf.argmax(y_conv, 1), tf.argmax(y, 1))  #ORIGINAL
    correct_prediction = tf.equal(tf.argmax(outputs, 1), tf.argmax(y, 1))

    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

    merged_summary_op = tf.summary.merge_all()

    return train_step, cross_entropy, accuracy, merged_summary_op


def train(x, keep_prob, y, train_step, accuracy, saver):
    val_step = 0
    loaded_data = load_training_data()
    # split into data windows:
    data_window_list = list(moving_window(loaded_data, DATA_WINDOW_SIZE, MOVING_WINDOW_SHIFT))
    shape = np.asarray(data_window_list).shape
    print("dataWindowList.shape (windows, window length, columns)", shape)
    x_list = []
    y_list = []
    for data_window in data_window_list:
        data_window_array = np.asarray(data_window)
        # TODO: Replace 2 & other constants with NUMBER_DATA_CHANNELS as needed
        count_match = np.count_nonzero(data_window_array[:, 2] == data_window_array[0, 2])
        # print("count_match: ", count_match)
        if count_match == shape[1]:
            x_window = data_window_array[:, 0:2:1]
            # TODO: NEED TO CHANGE PREPROCESSING TO BUTTERWORTH FILTER.
            # USE SAME FILTER AS IN ANDROID (C++ filt params),
            # Will need to pass through that filter in Android before feeding to model.
            mm_scale = preprocessing.MinMaxScaler().fit(x_window)
            x_window = mm_scale.transform(x_window)
            x_list.append(x_window)
            y_list.append(data_window_array[0, 2])

    init_op = tf.global_variables_initializer()

    # get unique class values and convert to dummy values
    # convert lists to arrays; convert to 32-bit floating point
    y_array = np.asarray(pd.get_dummies(y_list).values).astype(np.float32)
    x_array = np.asarray(x_list).astype(np.float32)

    x_train, x_test, y_train, y_test = train_test_split(x_array, y_array, train_size=0.9, random_state=1)

    with tf.Session() as sess:
        sess.run(init_op)
        # save model as pbtxt:
        tf.train.write_graph(sess.graph_def, EXPORT_DIRECTORY, MODEL_NAME + '.pbtxt', True)

        for i in range(NUMBER_STEPS):
            offset = (i * TRAIN_BATCH_SIZE) % (x_train.shape[0] - TRAIN_BATCH_SIZE)
            batch_x_train = x_train[offset:(offset + TRAIN_BATCH_SIZE)]
            shape_original = batch_x_train.shape
            # print("shape_original", shape_original)
            batch_x_train = np.reshape(batch_x_train,
                                       (shape_original[0], shape_original[1]*shape_original[2], -1)).squeeze()
            # print("shape_new", batch_x_train.shape)
            batch_y_train = y_train[offset:(offset + TRAIN_BATCH_SIZE)]
            if i % 10 == 0:
                # train_accuracy = accuracy.eval(feed_dict=
                #                                {x: batch_x_train, y: batch_y_train, keep_prob: 1.0})  # ORIGINAL
                train_accuracy = accuracy.eval(feed_dict={x: batch_x_train, y: batch_y_train, keep_prob: 1.0})
                print("step %d, training accuracy %g" % (i, train_accuracy))

            if i % 20 == 0:
                # Calculate batch loss and accuracy
                offset = (val_step * VAL_BATCH_SIZE) % (x_test.shape[0] - VAL_BATCH_SIZE)
                batch_x_val = x_test[offset:(offset + VAL_BATCH_SIZE), :, :]
                shape_original = batch_x_val.shape
                batch_x_val = np.reshape(batch_x_val,
                                         (shape_original[0], shape_original[1] * shape_original[2], -1)).squeeze()
                batch_y_val = y_test[offset:(offset + VAL_BATCH_SIZE), :]
                val_accuracy = accuracy.eval(feed_dict={x: batch_x_val, y: batch_y_val, keep_prob: 1.0})
                print("Validation step %d, validation accuracy %g" % (val_step, val_accuracy))
                val_step += 1

            train_step.run(feed_dict={x: batch_x_train, y: batch_y_train, keep_prob: 0.15})
        shape_original = x_test.shape
        x_test = np.reshape(x_test, (shape_original[0], shape_original[1] * shape_original[2], -1)).squeeze()
        test_accuracy = sess.run(accuracy, feed_dict={x: x_test, y: y_test, keep_prob: 1.0})
        print("\n Testing Accuracy:", test_accuracy, "\n\n")

        # save temp checkpoint
        saver.save(sess, EXPORT_DIRECTORY + MODEL_NAME + '.ckpt')


def export_model(input_node_names, output_node_name):
    freeze_graph.freeze_graph(EXPORT_DIRECTORY + MODEL_NAME + '.pbtxt', None, False,
                              EXPORT_DIRECTORY + MODEL_NAME + '.ckpt', output_node_name, "save/restore_all",
                              "save/Const:0", EXPORT_DIRECTORY + '/frozen_' + MODEL_NAME + '.pb', True, "")

    input_graph_def = tf.GraphDef()
    with tf.gfile.Open(EXPORT_DIRECTORY + '/frozen_' + MODEL_NAME + '.pb', "rb") as f:
        input_graph_def.ParseFromString(f.read())

    output_graph_def = optimize_for_inference_lib.optimize_for_inference(
        input_graph_def, input_node_names, [output_node_name], tf.float32.as_datatype_enum)

    with tf.gfile.FastGFile(EXPORT_DIRECTORY + '/opt_' + MODEL_NAME + '.pb', "wb") as f:
        f.write(output_graph_def.SerializeToString())

    print("Graph Saved - Output Directories: ")
    print("1 - Standard Frozen Model:", EXPORT_DIRECTORY + '/frozen_' + MODEL_NAME + '.pb')
    print("2 - Android Optimized Model:", EXPORT_DIRECTORY + '/opt_' + MODEL_NAME + '.pb')


def main():
    output_folder_name = 'exports'
    if not path.exists(output_folder_name):
        os.mkdir(output_folder_name)

    input_node_name = 'input'
    keep_prob_node_name = 'keep_prob'
    output_node_name = 'output'

    x, keep_prob, y_ = model_input(input_node_name, keep_prob_node_name)

    train_step, loss, accuracy, merged_summary_op = build_model(x, keep_prob, y_, output_node_name)

    saver = tf.train.Saver()

    train(x, keep_prob, y_, train_step, accuracy, saver)

    user_input = input('Export Current Model?')

    if user_input == "1" or user_input.lower() == "y":
        export_model([input_node_name, keep_prob_node_name], output_node_name)

    print("Terminating...")


if __name__ == '__main__':
    main()
