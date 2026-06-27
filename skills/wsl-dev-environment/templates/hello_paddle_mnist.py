"""
Hello Paddle — 手写数字识别 (MNIST) 模板
PaddlePaddle 3.3.0+ 兼容版本，已处理 labels squeeze / numpy scalar / astype 等坑。
"""
import paddle
import paddle.nn as nn
import paddle.optimizer as optim
from paddle.vision import transforms

BATCH_SIZE = 64
EPOCHS = 5
LEARNING_RATE = 0.001

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5]),
])

train_dataset = paddle.vision.datasets.MNIST(mode='train', transform=transform)
test_dataset = paddle.vision.datasets.MNIST(mode='test', transform=transform)

train_loader = paddle.io.DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = paddle.io.DataLoader(test_dataset, batch_size=BATCH_SIZE)


class LeNet(nn.Layer):
    def __init__(self, num_classes=10):
        super().__init__()
        self.conv1 = nn.Conv2D(1, 6, 5, padding=2)
        self.pool1 = nn.MaxPool2D(2, 2)
        self.conv2 = nn.Conv2D(6, 16, 5)
        self.pool2 = nn.MaxPool2D(2, 2)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, num_classes)

    def forward(self, x):
        x = self.pool1(nn.functional.relu(self.conv1(x)))
        x = self.pool2(nn.functional.relu(self.conv2(x)))
        x = paddle.flatten(x, start_axis=1)
        x = nn.functional.relu(self.fc1(x))
        x = nn.functional.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def train():
    model = LeNet()
    model.train()
    optimizer = optim.Adam(parameters=model.parameters(), learning_rate=LEARNING_RATE)
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(EPOCHS):
        total_loss = 0
        correct = 0
        total = 0

        for images, labels in train_loader():
            labels = labels.squeeze()  # 3.3.0: labels 是 (N,1) 需 squeeze
            logits = model(images)
            loss = loss_fn(logits, labels)

            loss.backward()
            optimizer.step()
            optimizer.clear_grad()

            total_loss += loss.numpy().item()  # 3.3.0: numpy() 返回标量，用 .item()
            correct += int((logits.argmax(1) == labels).astype('int64').sum().numpy())
            total += labels.shape[0]

        acc = correct / total
        avg_loss = total_loss / len(train_loader)
        print(f"Epoch {epoch+1}: loss={avg_loss:.4f}, acc={acc:.4f}")

    return model


def evaluate(model):
    model.eval()
    correct = 0
    total = 0

    for images, labels in test_loader():
        labels = labels.squeeze()
        logits = model(images)
        correct += int((logits.argmax(1) == labels).astype('int64').sum().numpy())
        total += labels.shape[0]

    acc = correct / total
    print(f"Test Accuracy: {acc:.4f} ({correct}/{total})")
    return acc


if __name__ == "__main__":
    print(f"PaddlePaddle {paddle.__version__} | GPU: {paddle.is_compiled_with_cuda()}")
    model = train()
    evaluate(model)
    paddle.save(model.state_dict(), "output/mnist_lenet.pdparams")
