# Copyright 2018-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
"""Convolutional Neural Network Estimator for MNIST, built with tensorflow.keras.layers."""

import numpy as np
import tensorflow as tf
import os,json,argparse
from tensorflow.keras.layers import *
from tensorflow.keras.models import *
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import categorical_crossentropy


def model():
    model = Sequential()
    model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)))
    model.add(MaxPooling2D((2, 2)))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2, 2)))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    model.add(Flatten())
    model.add(Dense(64, activation='relu'))
    model.add(Dense(10, activation='softmax'))
    model.compile(optimizer=Adam(lr=0.0001),metrics=['accuracy'],loss="categorical_crossentropy")
    return model

def _load_mnist_data(base_dir, x, y):
    x_data = np.load(os.path.join(base_dir, x)).reshape(-1,28,28,1)
    y_data = np.identity(10)[np.load(os.path.join(base_dir, y))]
    return x_data, y_data

def _parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_dir', type=str)
    parser.add_argument('--sm-model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--training', type=str, default=os.environ.get('SM_CHANNEL_TRAINING'))
    parser.add_argument('--hosts', type=list, default=json.loads(os.environ.get('SM_HOSTS')))
    parser.add_argument('--current-host', type=str, default=os.environ.get('SM_CURRENT_HOST'))
    parser.add_argument('--epochs', type=int, default=os.environ.get('SM_CURRENT_HOST'))
    parser.add_argument('--batch-size', type=int, default=os.environ.get('SM_CURRENT_HOST'))


    return parser.parse_known_args()


if __name__ == "__main__":
    args, unknown = _parse_args()

    x_train, y_train = _load_mnist_data(args.training, 'train_data.npy', 'train_labels.npy')
    x_valid, y_valid = _load_mnist_data(args.training,'eval_data.npy', 'eval_labels.npy' )

    # Create the Estimator
    mnist_classifier = model()
    # training
    mnist_classifier.fit(
        x_train,
        y_train,
        batch_size=args.batch_size,
        epochs=args.epochs,
        validation_data=(x_valid,y_valid)
    )

    save_model_path = os.path.join(args.sm_model_dir, '000000001')

    if args.current_host == args.hosts[0]:
        mnist_classifier.save(save_model_path)
