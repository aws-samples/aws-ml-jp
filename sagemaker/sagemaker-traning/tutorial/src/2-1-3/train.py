import tensorflow as tf
from keras import backend as K
K.set_image_data_format('channels_last')
import os
import numpy as np

# データロード
train_dir = os.environ.get('SM_CHANNEL_TRAIN')
valid_dir = os.environ.get('SM_CHANNEL_VALID')
x_train = np.load(os.path.join(train_dir,'x_train.npy'))
y_train = np.load(os.path.join(train_dir,'y_train.npy'))
x_valid = np.load(os.path.join(valid_dir,'x_valid.npy'))
y_valid = np.load(os.path.join(valid_dir,'y_valid.npy'))

# モデル定義
model = tf.keras.models.Sequential()
model.add(tf.keras.layers.Conv2D(filters=16,kernel_size=(3,3),padding="same",activation="relu",input_shape=(x_train.shape[1],x_train.shape[2],x_train.shape[3])))
model.add(tf.keras.layers.Flatten())
model.add(tf.keras.layers.Dense(10,activation="softmax"))
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.00001),metrics=['accuracy'],loss="sparse_categorical_crossentropy")

# トレーニング
model.fit(x_train,y_train,batch_size=4,epochs=2,validation_data=(x_valid,y_valid))

# モデルの保存
model_dir = os.environ.get('SM_MODEL_DIR')
model.save(os.path.join(model_dir,'1'))