---
name: indextts-local
description: WSL 本地部署 Index-TTS 语音合成服务 — 环境搭建、模型下载、FastAPI 封装、AstrBot 插件接入
---

# Index-TTS 本地部署（WSL + CUDA）

在 WSL 笔记本上部署 B 站 IndexTTS2 模型作为语音合成 HTTP 服务，对接 AstrBot QQ 机器人。

## 硬性要求

- WSL + NVIDIA GPU（本机 RTX 4070 8GB VRAM）
- CUDA Driver ≥ 12.8（验证：`nvidia-smi`）
- Python 3.12（不能用 3.14，PyTorch 等不支持）
- `uv` 包管理器

## 项目结构

```
~/projects/indextts-bot/
├── server/
│   ├── server.py          # FastAPI 服务（模型加载 + API）
│   └── static/
│       └── upload.html    # 角色音频上传页面
└── index-tts/             # github.com/index-tts/index-tts
    ├── checkpoints/       # 模型权重（~6.5GB）
    │   ├── gpt.pth        # 主模型
    │   ├── s2mel.pth      # 语音合成
    │   └── hf_cache/      # 辅助模型（自动下载）
    ├── prompts/           # 角色参考音频（voice_*.wav）
    └── start.sh           # 启动脚本
```

## 环境搭建

### 1. Python + CUDA

```bash
# 用 uv 管理 Python 3.12
cd ~/projects/indextts-bot
git clone https://github.com/index-tts/index-tts.git
cd index-tts
echo "3.12" > .python-version
uv venv --python 3.12
```

### 2. CUDA 运行时库

WSL 只提供 `libcuda.so`（驱动层），缺少 `libcudart.so`（运行时）。PyTorch 的 `nvidia-cuda-runtime` pip 包提供。

**关键：设置 LD_LIBRARY_PATH**，把 nvidia pip 包的 lib 目录加进去：

```bash
NVIDIA_LIB=$(find ~/.local/share/uv/python/cpython-3.12.*/lib/python3.12/site-packages/nvidia -name lib -type d | tr '\n' ':')/usr/lib/wsl/lib
export LD_LIBRARY_PATH="$NVIDIA_LIB"
```

详见 [references/cuda-runtime.md](references/cuda-runtime.md)。

### 3. PYTHONPATH 污染

**致命坑**：Hermes Agent 环境设置了全局 `PYTHONPATH=/home/po/.hermes/hermes-agent`，导致所有 Python 的 sys.path 都被污染。运行 Index-TTS 时必须 unset：

```bash
unset PYTHONPATH  # 或 PYTHONPATH= command
```

### 4. 安装依赖

```bash
# 清华镜像（直连 PyPI 太慢）
uv pip install -i https://download.pytorch.org/whl/cu130 torch torchaudio \
  --extra-index-url https://pypi.tuna.tsinghua.edu.cn/simple

uv pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
  librosa numpy==1.26.2 scipy==1.11.4 transformers==4.52.1 \
  safetensors sentencepiece tokenizers omegaconf opencv-python \
  pandas einops ffmpeg-python json5 jieba keras accelerate \
  cython WeTextProcessing scikit-learn matplotlib \
  fastapi soundfile python-multipart modelscope huggingface_hub \
  uvicorn descript-audiotools numba textstat g2p-en cn2an
```

**注意版本**：
- `transformers` 必须 `==4.52.1`（IndexTTS2 内部代码依赖特定 API）
- `numpy` 必须 `<=1.26.2`（numba 兼容性）
- `scipy` 必须 `<=1.11.4`（配合 numpy 1.x）
- torch 用 `cu130` 索引（适配 CUDA 13 driver）

## 模型下载

### 主模型（IndexTTS-2）

modelscope Python SDK 最可靠（git LFS 和 HF-mirror 经常断）：

```python
from modelscope import snapshot_download
snapshot_download('IndexTeam/IndexTTS-2', cache_dir='/tmp/ms_cache', local_dir='checkpoints')
```

大文件清单（确认都有）：
- `gpt.pth` ~3.3GB
- `s2mel.pth` ~1.2GB
- `qwen0.6bemo4-merge/model.safetensors` ~1.2GB

### 辅助模型（首次运行时自动下载）

这些不在 checkpoints 里，IndexTTS2 首次 `__init__` 时自动下载到 `checkpoints/hf_cache/`：
- `w2v-bert-2.0/` (conformer_shaw.pt 1.4G, model.safetensors 1.2G)
- `bigvgan/` (bigvgan_generator.pt ~170M)
- `semantic_codec_model.safetensors` ~169M
- `campplus_cn_common.bin` ~27M

**注意**：modelscope 可能找不到 BigVGAN 仓库（`nvidia/bigvgan_v2_22khz_80band_256x`），需手动从 HuggingFace 下载：

```python
from huggingface_hub import hf_hub_download
hf_hub_download('nvidia/bigvgan_v2_22khz_80band_256x', 'bigvgan_generator.pt',
    local_dir='checkpoints/hf_cache/bigvgan')
```

## 服务启动

```bash
cd ~/projects/indextts-bot/index-tts
NVIDIA_LIB=$(find ~/.local/share/uv/python/cpython-3.12.*/lib/python3.12/site-packages/nvidia -name lib -type d 2>/dev/null | tr '\n' ':')/usr/lib/wsl/lib
PYTHONPATH= LD_LIBRARY_PATH="$NVIDIA_LIB" TMPDIR=/home/po/tmp \
  ~/.local/share/uv/python/cpython-3.12.*/bin/python3.12 \
  /home/po/projects/indextts-bot/server/server.py
```

首次加载需 ~35 秒。启动后：
- API health：`GET /api/health`
- 上传页面：`http://localhost:8800`
- 语音合成：`POST /api/tts {"text":"你好","voice_name":"xxx"}`
- 角色管理：`GET/POST/DELETE /api/voices`

## 持久化运行

用 tmux 保持（systemd 暂未配置）：

```bash
# 启动
tmux new-session -d -s tts "cd ~/projects/indextts-bot/index-tts && ... server.py"
# 查看日志
tmux capture-pane -t tts -p | tail -10
# 停止
tmux kill-session -t tts
```

## AstrBot 插件

插件 `astrbot_plugin_indextts` 已部署在 `data/plugins/`，通过 HTTP 调用本地 TTS 服务。

插件命令：
- `/注册语音 <角色名>` — 提示去 `http://localhost:8800` 上传
- `/语音列表` — 查看已注册角色
- `/语音 <角色名> <文本>` — 手动合成
- `/开启语音 <角色名>` — 开启自动 TTS

**注意**：AstrBot v4.26 的插件 API 变更：
- `@filter.on_message()` 不存在 → 用 `@filter.event_message_type(EventMessageType.ALL)`
- `from astrbot.api.event.filter import EventMessageType`
- 新插件需重启 AstrBot 或调 `/api/plugin/reload-failed`（需 Bearer token）

## 坑汇总

| 坑 | 症状 | 解决 |
|----|------|------|
| PYTHONPATH 污染 | sys.path 含 `/home/po/.hermes/hermes-agent` | `unset PYTHONPATH` |
| librosa/lazy_loader 报错 | numba 需要 numpy<=1.26 | `pip install numpy==1.26.2 scipy==1.11.4` |
| CUDA 运行时缺失 | `libcudart.so.12: cannot open` | 把 nvidia pip libs 加到 LD_LIBRARY_PATH |
| uvicorn lifespan 超时 | 模型加载 >5s 导致启动失败 | 在 `__main__` 中加载，lifespan 只做 yield |
| `__main__` vs 模块双加载 | 模型加载两次炸显存 | 用 `uvicorn.run(app, ...)` 而非 `"server:app"` |
| transformers 5.x | `cannot import OffloadedCache` | 必须 `transformers==4.52.1` |
| HF/git LFS 下载 | 长时间无进展 | 用 modelscope Python SDK |
| 磁盘 tmpfs 满 | pip 安装时 `No space left` | `/tmp` 是 tmpfs，设 `TMPDIR=/home/po/tmp` |
| git lfs pull 静默失败 | 大文件指针未 resolve | 放弃 git LFS，用 modelscope SDK |
| BigVGAN CUDA kernel | `Failed to load custom CUDA kernel` | 非致命，自动 fallback 到 torch |
