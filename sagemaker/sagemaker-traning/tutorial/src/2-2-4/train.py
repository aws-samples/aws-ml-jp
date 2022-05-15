import torch
import torchvision
import os, json

# ハイパーパラメータ取得
hps = json.loads(os.environ.get('SM_HPS'))
hps.setdefault('batch_size', 4)
hps.setdefault('epochs', 2)
hps.setdefault('filters', 16)
hps.setdefault('learning_rate', 0.00001)
print(hps)

# データロード
train_dir = os.environ.get('SM_CHANNEL_TRAIN')
valid_dir = os.environ.get('SM_CHANNEL_VALID')
train_data = torch.utils.data.TensorDataset(*torch.load(os.path.join(train_dir, 'train.pt')))
train_data_loader = torch.utils.data.DataLoader(train_data, batch_size=hps['batch_size'], shuffle=True, num_workers=2)
valid_data = torch.utils.data.TensorDataset(*torch.load(os.path.join(valid_dir, 'valid.pt')))
valid_data_loader = torch.utils.data.DataLoader(valid_data, batch_size=hps['batch_size'], shuffle=True, num_workers=2)


#モデル定義
model = torch.nn.Sequential(
    torch.nn.Conv2d(3, hps['filters'], kernel_size=(3,3), stride=1, padding=(1,1)),
    torch.nn.ReLU(),
    torch.nn.Flatten(),
    torch.nn.Linear(hps['filters']*32*32,10),
    torch.nn.Softmax(dim=1)
)

# 学習
def exec_epoch(loader, model, train_flg, optimizer, criterion):
    total_loss = 0.0
    correct = 0
    count = 0
    for i, data in enumerate(loader, 0):
        inputs, labels = data
        if train_flg:
            inputs, labels = torch.autograd.Variable(inputs), torch.autograd.Variable(labels)
            optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        if train_flg:
            loss.backward()
            optimizer.step()
        total_loss += loss.item()
        pred_y = outputs.argmax(axis=1)
        correct += sum(labels==pred_y)
        count += len(labels)
    total_loss /= (i+1)
    total_acc = 100 * correct / count
    if train_flg:
        print(f'train_loss: {total_loss:.3f} train_acc: {total_acc:.3f}%',end=' ')
    else:
        print(f'valid_loss: {total_loss:.3f} valid_acc: {total_acc:.3f}%')
    return model

criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(params=model.parameters(), lr=hps['learning_rate'])
for epoch in range(hps['epochs']):
    print(f'epoch: {epoch+1}',end=' ')
    model = exec_epoch(train_data_loader, model, True, optimizer, criterion)
    exec_epoch(valid_data_loader, model, False, optimizer, criterion)

# モデル保存
model_dir = os.environ.get('SM_MODEL_DIR')
torch.save(model.state_dict(),os.path.join(model_dir,'1.pth'))