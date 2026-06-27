# PaddlePaddle (飞桨) 在 WSL 上的安装

## 版本信息

- 最新稳定版：3.3.0（截至 2026.06）
- Python 支持：3.9–3.13（**不支持 3.14**）
- 官方安装索引：https://www.paddlepaddle.org.cn/packages/stable/

## CPU 版安装（WSL 无 GPU 时）

```bash
# 1. 用 uv 创建 Python 3.12 venv（3.12 兼容性最好）
uv venv --python 3.12 /home/po/.venvs/paddle

# 2. 激活
source /home/po/.venvs/paddle/bin/activate

# 3. 安装（必须用飞桨官方源，PyPI 上可能没有最新版）
uv pip install paddlepaddle==3.3.0 \
  -i https://www.paddlepaddle.org.cn/packages/stable/cpu/

# 4. 验证
python -c "import paddle; print(paddle.__version__); paddle.utils.run_check()"
# 期望输出：3.3.0 + "PaddlePaddle is installed successfully!"
```

## GPU 版安装（有 CUDA 时）

```bash
# CUDA 13.0
uv pip install paddlepaddle-gpu==3.3.0 \
  -i https://www.paddlepaddle.org.cn/packages/stable/cu130/

# CUDA 12.6
uv pip install paddlepaddle-gpu==3.3.0 \
  -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# CUDA 11.8
uv pip install paddlepaddle-gpu==3.3.0 \
  -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
```

## 常见警告（可忽略）

- `No ccache found` — 不影响使用，只是编译缓存工具缺失
- `Tensor do not have 'place' interface` — PIR 图模式下的正常警告

## 验证脚本

```python
import paddle

# 版本
print(paddle.__version__)          # 3.3.0

# 环境检查
paddle.utils.run_check()           # 输出 CPU 核心数 + 成功信息

# 可用设备
print(paddle.device.get_device())  # cpu
print(paddle.is_compiled_with_cuda())  # False on CPU install
```

## WSL GPU 版配置

### 前置条件

- WSL2（`uname -r` 含 `microsoft-standard-WSL2`）
- NVIDIA GPU 驱动 ≥ 545.23.06（可在 Windows 侧 `nvidia-smi` 查看）
- WSL 内需有 `/usr/lib/wsl/lib/libcuda.so`（WSL GPU 直通）
- 飞桨 3.3.0 自带 CUDA+cuDNN，**不需要**在 WSL 内单独装 CUDA toolkit

### 安装命令

```bash
# RTX 30/40 系列推荐 CUDA 12.6（最稳）
uv pip install paddlepaddle-gpu==3.3.0 \
  -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# 或 CUDA 13.0（需驱动 ≥ 545.84）
uv pip install paddlepaddle-gpu==3.3.0 \
  -i https://www.paddlepaddle.org.cn/packages/stable/cu130/
```

### WSL libcuda.so 路径修复

WSL 的 libcuda.so 在 `/usr/lib/wsl/lib/`，不在默认 LD_LIBRARY_PATH。虽不影响运行（飞桨会自动找到），但会打印警告。消除方法——在 venv 的 `activate` 脚本末尾 `hash -r` 之前加入：

```bash
_OLD_VIRTUAL_LD_LIBRARY_PATH="$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/usr/lib/wsl/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

> 注意：`uv` 创建的 venv 每次 `uv sync` 或其他操作可能重建 activate，需重新检查。

### GPU 验证

```python
import paddle
print(paddle.is_compiled_with_cuda())    # True
print(paddle.device.cuda.device_count()) # 1
print(paddle.device.cuda.get_device_name(0))  # GPU 名称

# 简单张量测试
x = paddle.randn([3,3])
y = paddle.randn([3,3])
z = paddle.matmul(x, y)
print(z.place)  # Place(gpu:0) 说明在 GPU 上运行
```

### 支持的 CUDA 版本

| CUDA | 飞桨源 | 推荐场景 |
|------|--------|---------|
| 11.8 | `.../cu118/` | 旧卡 / 兼容性优先 |
| 12.6 | `.../cu126/` | RTX 30/40 系列首选 |
| 12.9 | `.../cu129/` | Hopper/Blackwell |
| 13.0 | `.../cu130/` | Blackwell / 最新驱动 |

## 飞桨 3.3.0 API 已知坑

以下问题在 3.3.0 上遇到，来自 PaddlePaddle 对 NumPy 2.x 和动态图机制的变更。

### MNIST labels 是 (N, 1) 而非 (N,)

`paddle.vision.datasets.MNIST` 返回的 labels shape 为 `(batch_size, 1)`，直接与 `logits.argmax(1)` 比较会因广播产生错误结果（准确率 >100%）。

**修复**：训练/评估循环中 `squeeze()` 掉多余维度。

```python
for images, labels in train_loader():
    labels = labels.squeeze()  # (64,1) → (64,)
    logits = model(images)
    ...
```

### loss.numpy() 返回 0 维标量

`loss.numpy()` 在旧版返回 1 维数组可用 `[0]` 取值，3.3.0 返回标量——`[0]` 报 `IndexError: too many indices for array`。

**修复**：用 `.item()` 或 `int()`。

```python
# 错误
total_loss += loss.numpy()[0]

# 正确
total_loss += loss.numpy().item()
total_loss += float(loss.numpy())
```

### astype('int') 行为变更

`tensor.astype('int')` 在 3.3.0 可能产生非预期类型导致 `sum()` 结果异常。

**修复**：显式使用 `'int64'`。

```python
# 可能异常
(logits.argmax(1) == labels).astype('int').sum().numpy()

# 正确
int((logits.argmax(1) == labels).astype('int64').sum().numpy())
```
