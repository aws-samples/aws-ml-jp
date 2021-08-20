import tensorflow as tf
import numpy as np
import os
from keras.models import Model,Sequential,load_model
from keras.layers import Input,Conv2D,LeakyReLU,Dense,Reshape,Flatten,Dropout,BatchNormalization,Conv2DTranspose,MaxPool2D
from keras.activations  import sigmoid
from keras.datasets import fashion_mnist
from keras.optimizers import Adam
import argparse, json
from distutils.util import strtobool

MODEL_FILE_NAME = 'classifier.h5'

def classifier():
    inputs = Input(shape=(28,28,1))
    x = Conv2D(64, (3,3),padding='same')(inputs)
    x = BatchNormalization()(x)
    x = LeakyReLU(0.2)(x)
    x = MaxPool2D(pool_size=(2, 2))(x) # 14x14
    x = Conv2D(64, (3,3),padding='same')(x)
    x = BatchNormalization()(x)
    x = LeakyReLU(0.2)(x)
    x = MaxPool2D(pool_size=(2, 2))(x) # 7x7
    x = Conv2D(128, (3,3),padding='same')(x)
    x = BatchNormalization()(x)
    x = LeakyReLU(0.2)(x)
    x = MaxPool2D(pool_size=(2, 2))(x)
    x = Conv2D(128, (3,3),padding='same')(x)
    x = BatchNormalization()(x)
    x = LeakyReLU(0.2)(x)
    x = MaxPool2D(pool_size=(2, 2))(x)
    x = Flatten()(x)
    x = Dense(128)(x)
    x = LeakyReLU(0.2)(x)
    x = BatchNormalization()(x)
    x = Dropout(0.5)(x)
    x = Dense(10, activation='softmax')(x)
    model = Model(inputs=inputs, outputs=x)
    model.summary()
    return model
    
def train(train_x,train_y,valid_x,valid_y,epochs,model_dir,increment,base_dir):
    if increment:
        model = load_model(os.path.join(base_dir, MODEL_FILE_NAME))
    else:
        model = classifier()
    model.compile(optimizer=Adam(lr=0.0001),metrics=['accuracy'],loss="categorical_crossentropy")
    model.fit(train_x,train_y,batch_size=16,epochs=epochs,validation_data=(valid_x,valid_y))
    
    save_model_path = os.path.join(model_dir, MODEL_FILE_NAME)
    model.save(save_model_path)
    
    return model

def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_dir', type=str)
    parser.add_argument('--sm-model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN'))
    parser.add_argument('--hosts', type=list, default=json.loads(os.environ.get('SM_HOSTS')))
    parser.add_argument('--current-host', type=str, default=os.environ.get('SM_CURRENT_HOST'))
    parser.add_argument('--epochs', type=int, default=2)
    parser.add_argument('--increment', type=strtobool ,default=False)

    return parser.parse_known_args()

def load_training_data(base_dir):
    X = np.load(os.path.join(base_dir, 'train_X.npy'))
    y = np.load(os.path.join(base_dir, 'train_y.npy'))
    # shuffle and split
    shuffle_index = np.random.choice(np.arange(X.shape[0]), X.shape[0], replace=False)
    train_X = X[shuffle_index[0:50000]]
    train_y = y[shuffle_index[0:50000]]
    valid_X = X[shuffle_index[50000:]]
    valid_y = y[shuffle_index[50000:]]
    
    return train_X, train_y, valid_X, valid_y

if __name__ == "__main__":
    args, unknown = _parse_args()
    print(args)
    train_X, train_y, valid_X, valid_y = load_training_data(args.train)
    model = train(train_X, train_y, valid_X, valid_y,args.epochs,args.sm_model_dir,args.increment,args.train)

    exit()