
import lightgbm as lgb
import os, json
import numpy as np
from sklearn.metrics import accuracy_score, classification_report

hps = json.loads(os.environ.get('SM_HPS'))
num_leaves = hps.get("num_leaves",10)

# データロード
train_dir = os.environ.get('SM_CHANNEL_TRAIN')
valid_dir = os.environ.get('SM_CHANNEL_VALID')
x_train = np.load(os.path.join(train_dir,'x_train.npy'))
y_train = np.load(os.path.join(train_dir,'y_train.npy'))
x_valid = np.load(os.path.join(valid_dir,'x_valid.npy'))
y_valid = np.load(os.path.join(valid_dir,'y_valid.npy'))

# 画像データを1次元に変換 (32x32x3 = 3072次元)
x_train = x_train.reshape(x_train.shape[0], -1)
x_valid = x_valid.reshape(x_valid.shape[0], -1)

# ラベルを1次元に変換
y_train = y_train.flatten()
y_valid = y_valid.flatten()

# データ型を変換
x_train = x_train.astype('float32')
x_valid = x_valid.astype('float32')

# 正規化 (0-255 → 0-1)
x_train /= 255.0
x_valid /= 255.0

# LightGBMデータセットの作成
train_data = lgb.Dataset(x_train, label=y_train)
val_data = lgb.Dataset(x_valid, label=y_valid, reference=train_data)

# LightGBMパラメータの設定
params = {
    'objective': 'multiclass',
    'num_class': 10,
    'metric': 'multi_logloss',
    'boosting_type': 'gbdt',
    'num_leaves': num_leaves,
    'learning_rate': 0.05,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': 0,
    'random_state': 42
}

model = lgb.train(
    params,
    train_data,
    valid_sets=[train_data, val_data],
    valid_names=['train', 'eval'],
    num_boost_round=3,
    callbacks=[
        lgb.early_stopping(stopping_rounds=50),
        lgb.log_evaluation(period=100)
    ]
)

# 予測
y_pred = model.predict(x_valid, num_iteration=model.best_iteration)
y_pred_class = np.argmax(y_pred, axis=1)

# 精度の評価
accuracy = accuracy_score(y_valid, y_pred_class)
print(f"accuracy: {accuracy:.4f}")


model_dir = os.environ.get('SM_MODEL_DIR')
model.save_model(os.path.join(model_dir, 'cifer10.txt'))
