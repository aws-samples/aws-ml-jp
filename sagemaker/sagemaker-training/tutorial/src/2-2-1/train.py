import torch
import torchvision

# データロード
train_data = torchvision.datasets.CIFAR10(root='./data', train=True,download=True, transform=torchvision.transforms.Compose([torchvision.transforms.ToTensor()]))
train_data_loader = torch.utils.data.DataLoader(train_data, batch_size=4, shuffle=True, num_workers=2)
valid_data = torchvision.datasets.CIFAR10(root='./data', train=False,download=True, transform=torchvision.transforms.Compose([torchvision.transforms.ToTensor()]))
valid_data_loader = torch.utils.data.DataLoader(valid_data, batch_size=4,shuffle=False, num_workers=2)

#モデル定義
model = torch.nn.Sequential(
    torch.nn.Conv2d(3, 16, kernel_size=(3,3), stride=1, padding=(1,1)),
    torch.nn.ReLU(),
    torch.nn.Flatten(),
    torch.nn.Linear(16*32*32,10),
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
optimizer = torch.optim.Adam(params=model.parameters(), lr=0.00001)
for epoch in range(2):
    print(f'epoch: {epoch+1}',end=' ')
    model = exec_epoch(train_data_loader, model, True, optimizer, criterion)
    exec_epoch(valid_data_loader, model, False, optimizer, criterion)

# モデル保存
torch.save(model.state_dict(),'1.pth')