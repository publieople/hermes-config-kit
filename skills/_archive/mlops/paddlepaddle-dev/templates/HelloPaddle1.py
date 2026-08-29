"""
HelloPaddle1.py — 老师的参考代码（高层 API 版本）
PaddlePaddle 3.x MNIST + LeNet 手写数字识别

这是最简洁正确的写法，作为实训模板参考。
运行: python HelloPaddle1.py
依赖: paddlepaddle>=3.0.0, numpy, matplotlib
"""
import paddle
import numpy as np
from paddle.vision.transforms import Normalize

transform = Normalize(mean=[127.5], std=[127.5], data_format="CHW")
train_dataset = paddle.vision.datasets.MNIST(mode="train", transform=transform)
test_dataset = paddle.vision.datasets.MNIST(mode="test", transform=transform)

lenet = paddle.vision.models.LeNet(num_classes=10)
model = paddle.Model(lenet)

model.prepare(
    paddle.optimizer.Adam(parameters=model.parameters()),
    paddle.nn.CrossEntropyLoss(),
    paddle.metric.Accuracy(),
)

model.fit(train_dataset, epochs=5, batch_size=64, verbose=1)
model.evaluate(test_dataset, batch_size=64, verbose=1)

model.save("./output/mnist")
model.load("output/mnist")

# 推理单张图片
img, label = test_dataset[0]
img_batch = np.expand_dims(img.astype("float32"), axis=0)
out = model.predict_batch(img_batch)[0]
pred_label = out.argmax()
print("true label: {}, pred label: {}".format(label[0], pred_label))

from matplotlib import pyplot as plt
plt.imshow(img[0])
