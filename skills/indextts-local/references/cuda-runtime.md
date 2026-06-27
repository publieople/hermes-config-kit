# WSL CUDA 运行时配置

## 问题

WSL 只提供 CUDA 驱动库（`libcuda.so`），不提供 CUDA 运行时（`libcudart.so`）。
PyTorch 的 `nvidia-cuda-runtime` pip 包提供了运行时库，但版本号可能不匹配。

## 本机配置

- **GPU**：NVIDIA GeForce RTX 4070 Laptop GPU (8GB)
- **Driver**：591.74 / CUDA 13.1
- **PyTorch**：2.12.1+cu130
- **nvidia-cuda-runtime**：13.0.96

## LD_LIBRARY_PATH

```bash
NVIDIA_SITE=~/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/lib/python3.12/site-packages/nvidia
NVIDIA_LIB=$(find "$NVIDIA_SITE" -name lib -type d | tr '\n' ':')/usr/lib/wsl/lib
export LD_LIBRARY_PATH="$NVIDIA_LIB"
```

这会包含：
- `nvidia/cu13/lib/` → libcudart.so.13, libcublas.so.13, ...
- `nvidia/cudnn/lib/` → libcudnn.so.9
- `nvidia/cufft/lib/` → libcufft.so.12
- `nvidia/nccl/lib/` → libnccl.so.2
- `nvidia/nvjitlink/lib/` → libnvJitLink.so.13
- `/usr/lib/wsl/lib/` → libcuda.so (WSL 驱动)

## 版本不匹配处理

如果 PyTorch 用 `cu128` 索引安装（`torch-2.12.1+cu128`），但 nvidia-cuda-runtime 是 13.0，
会出现 `libcudart.so.12: cannot open shared object file`。

**解决**：改用 `cu130` 索引重装：
```bash
pip install --force-reinstall -i https://download.pytorch.org/whl/cu130 torch torchaudio
```

## 特殊处理（仅 cu128 索引）

如果必须用 cu128，可以在 nvidia pip lib 目录下创建符号链接：
```bash
cd $NVIDIA_SITE/cu13/lib
ln -sf libcudart.so.13 libcudart.so.12
```
但注意 SONAME 检查可能仍然失败——推荐直接用 cu130。
