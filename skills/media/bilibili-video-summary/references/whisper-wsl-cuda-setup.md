# WSL CUDA 配置路径

## nvidia-smi

WSL 2 里 nvidia-smi 不在 PATH 里，完整路径：

```bash
/usr/lib/wsl/lib/nvidia-smi
```

## CUDA 库路径

```
/usr/lib/wsl/lib/libcuda.so
/usr/lib/wsl/lib/libcuda.so.1
/usr/lib/wsl/lib/libcuda.so.1.1
```

PyTorch 自动检测这些路径，不需要手动设置 LD_LIBRARY_PATH。

## 验证 GPU 可用

```bash
python -c "import torch; print(torch.cuda.is_available())"
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

## 性能实测（RTX 4070 Laptop, 8GB）

| 模型 | 3.5min 视频耗时 | 倍速 |
|------|:---:|:---:|
| GPU small | 45.5s | 0.21x |
| GPU medium | 95.3s | 0.45x |
| CPU base | ~200s | 0.94x |

**结论**：WSL CUDA 下 medium 反而慢于 small（可能是 WSL 的 GPU 调度开销对大模型更敏感）。4070 8GB 最优配置是 **small 模型**。

## 避坑

- `--device cuda` 是 whisper CLI 参数，脚本里已处理；Python API 用 `device='cuda'`
- 不要强设 `--language zh`：标题含中文不代表内容是中文。让 Whisper auto-detect
- 首次运行会下载模型到 `~/.cache/whisper/`，后续无需下载