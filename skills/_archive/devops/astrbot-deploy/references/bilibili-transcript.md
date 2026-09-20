# B站视频转录（bilibili-transcript）

## 核心引擎

脚本来源：ClawHub `bilibili-auto-transcript` v5.0（作者 54lynnn）
适配为 AstrBot skill：`~/astrbot/data/skills/bilibili-transcript/`

## 三级降级

1. **CC 字幕**（人工）→ 100% 准确，秒出
2. **AI 字幕**（9 语言）→ ~90% 准确，秒出
3. **Whisper 本地转录** → ~95% 准确，需 GPU/CPU

## B站 yt-dlp 412 反爬修复

B站 HTTP 412 `Precondition Failed` 是 API 限流/反爬。修复：加 Origin 头。

```bash
# 所有 yt-dlp 调用都需要这两个头
yt-dlp --add-header "Origin:https://www.bilibili.com" \
       --add-header "Referer:https://www.bilibili.com/" \
       --dump-json "$BV_URL"
```

## WSL GPU/CUDA 路径

| 项目 | 路径 |
|------|------|
| nvidia-smi | `/usr/lib/wsl/lib/nvidia-smi` |
| libcuda.so | `/usr/lib/wsl/lib/libcuda.so.1` |
| CUDA 版本 | 13.1 (driver 591.74) |
| PyTorch CUDA | cu128 (兼容 CUDA 13.x 驱动) |

## Whisper 模型缓存

`~/.cache/whisper/` 自动下载，首次慢后续快：

| 模型 | 大小 | GPU 速度 (3.5min 视频) |
|------|------|------------------------|
| tiny | 73MB | — |
| base | 139MB | — |
| small | — | **45s** (0.21x) |
| medium | 1.5GB | 95s (0.45x) |

## Whisper 语言检测避坑

**不要根据标题含中文就强设 `--language zh`**。英文视频有中文标题（如"【官方 MV】Never Gonna Give You Up"）会：
- 识别结果变成乱码
- 速度变慢（模型试图匹配中文音素）

正确做法：不传 `--language`，让 Whisper 自动检测（准确率极高）。

## 音频预处理

传给 Whisper 前统一转 `16kHz 单声道 WAV`：

```bash
ffmpeg -y -i input.mp3 -ar 16000 -ac 1 output.wav
```

## Python 3.12 venv（必须）

系统 Python 3.14 不兼容 openai-whisper（pkg_resources 已移除），必须用：

```bash
uv venv --python 3.12 .venv-cuda
uv pip install --python .venv-cuda/bin/python \
  --index-url https://download.pytorch.org/whl/cu128 torch
uv pip install --python .venv-cuda/bin/python \
  -i https://pypi.tuna.tsinghua.edu.cn/simple openai-whisper
```

## 输出

文件路径：`~/astrbot/data/transcripts/bilibili/<年份>/<月份>/<标题>_<作者>_<日期>_<avid>.txt`
