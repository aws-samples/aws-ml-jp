import tensorflow as tf
from keras import backend as K
K.set_image_data_format('channels_last')

# データロード
(x_train,y_train),(x_valid,y_valid) = tf.keras.datasets.cifar10.load_data()
print(x_train.shape)
x_train = (x_train/255)
x_valid = (x_valid/255)

# モデル定義
model = tf.keras.models.Sequential()
model.add(tf.keras.layers.Conv2D(filters=16,kernel_size=(3,3),padding="same",activation="relu",input_shape=(x_train.shape[1],x_train.shape[2],x_train.shape[3])))
model.add(tf.keras.layers.Flatten())
model.add(tf.keras.layers.Dense(10,activation="softmax"))

# トレーニング
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.00001),metrics=['accuracy'],loss="sparse_categorical_crossentropy")
model.fit(x_train,y_train,batch_size=4,epochs=2,validation_data=(x_valid,y_valid))

# モデルの保存
model.save('./1')
