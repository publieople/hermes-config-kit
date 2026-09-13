# IndexTTS / CosyVoice2 本地 TTS 部署

## 核心架构（TTS 服务独立模式）

TTS 模型部署为独立的 FastAPI 服务进程，AstrBot 插件作为 HTTP 客户端调用。这是推荐的解耦模式。

```
本机 GPU (WSL)
├── TTS FastAPI 服务 (port 5050 或 8800)
│   ├── IndexTTS-2 (需要 7-8GB VRAM，4070 8GB 勉强)
│   ├── IndexTTS-1 (需要 ~4GB VRAM，推荐)
│   └── CosyVoice2-0.5B (需要 ~0.8GB，最优但配置复杂)
└── AstrBot 插件 → HTTP → FastAPI 服务
```

## WSL CUDA 环境

WSL 原生支持 CUDA（通过 Windows 驱动转发），不需要在 WSL 内装独立 NVidia 驱动。

### 环境检查
```bash
# Windows 端 GPU 状态
/mnt/c/Windows/System32/nvidia-smi.exe

# WSL CUDA 库路径
ls /usr/lib/wsl/lib/libcuda*

# Python 中验证 CUDA
LD_LIBRARY_PATH=/usr/lib/wsl/lib python3 -c "import torch; print(torch.cuda.is_available())"
```

### 关键坑：libcudart.so 版本 mismatch

通过 pip 安装的 `torch`（CUDA 12.8 wheel）会自带 nvidia-* 包，但 libcudart 的 SONAME 可能不匹配。

**症状**：`OSError: libcudart.so.12: cannot open shared object file`

**修复**：创建软链接（CUDA 13 → 12 双向兼容）
```bash
# nvidia pip 包安装的 libcudart
ls ~/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/lib/python3.12/site-packages/nvidia/cu13/lib/libcudart*

# 创建 so.12 → so.13 链接
ln -sf libcudart.so.13 libcudart.so.12
```

**运行时需要设置 LD_LIBRARY_PATH** 包含 nvidia pip 包路径：
```bash
NVIDIA_LIB=$(find ~/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/lib/python3.12/site-packages/nvidia -name "lib" -type d 2>/dev/null | tr '\n' ':')
export LD_LIBRARY_PATH="${NVIDIA_LIB}/usr/lib/wsl/lib"
```

### 关键坑：PYTHONPATH 污染

Hermes Agent 在 WSL 环境变量中设置了 `PYTHONPATH=/home/po/.hermes/hermes-agent`，导致每个 Python 进程都会加载 hermes-agent 包。会引发：
- `pip install` 失败 with `hermes-agent requires xxx` warnings
- `uv pip install --python` 安装到错误位置
- 模型代码意外依赖 hermes-agent 的依赖

**修复**：run 前 unset
```bash
unset PYTHONPATH
uv run python ...
```

## IndexTTS-2 部署

### 环境搭建
```bash
git clone https://github.com/index-tts/index-tts.git
cd index-tts
uv sync --extra webui
```

### 模型下载
```bash
# 方法一：modelscope（国内推荐）
uv run python -c "from modelscope import snapshot_download; snapshot_download('IndexTeam/IndexTTS-2', local_dir='checkpoints')"

# 方法二：HuggingFace 镜像
HF_ENDPOINT=https://hf-mirror.com uv run huggingface-cli download IndexTeam/IndexTTS-2 --local-dir checkpoints
```

**Modelscope 下载坑**：
- `snapshot_download` 可能只下载元数据不下载 LFS 文件
- 验证 `checkpoints/gpt.pth` 是否真实文件 (>3GB)
- 若缺失，补下 `model_file_download` 单独下载

### 运行测试
```bash
cd index-tts
LD_LIBRARY_PATH=$NVIDIA_LIB:/usr/lib/wsl/lib \
PYTHONPATH= \
uv run python -c "
from indextts.infer_v2 import IndexTTS2
tts = IndexTTS2(model_dir='checkpoints', use_fp16=True)
print('OK:', tts.device)
"
```

### FastAPI 服务

服务代码放在 `~/projects/indextts-bot/server/server.py`。包含：
- `/api/health` — 健康检查
- `/api/voices` — 角色列表/注册/删除（multipart upload）
- `/api/tts` — 合成 POST `{text, voice_name, emo_text}`
- `/api/audio/<filename>` — 音频文件
- `/` — WebUI 上传页面

**启动**（需要 tmux 或 systemd 保持后台运行）：
```bash
tmux new-session -d -s tts "cd ~/projects/indextts-bot/index-tts && \
NVIDIA_LIB=... && PYTHONPATH= LD_LIBRARY_PATH=\"\$NVIDIA_LIB\" \
~/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/bin/python3.12 \
~/projects/indextts-bot/server/server.py"
```

### VRAM 问题（RTX 4070 8GB）

IndexTTS-2 FP16 加载后占用 ~6-7GB，推理时暴涨导致 OOM。

**症状**：`CUDA error: out of memory`

**解决办法**：
1. 改用 IndexTTS v1（轻量，~4GB）
2. 改用 CosyVoice2-0.5B（0.8GB）
3. 换更大显存的 GPU

## 设备管理

TTS 服务启动后，AstrBot 插件通过 `tts_api_url` 配置连接。

**参考音频**：放在 `prompts/voice_<name>.wav`（IndexTTS）或 `sounds/<name>.wav`（CosyVoice2）。
格式：mono, 16-bit PCM, 24kHz, 3-15 秒。
