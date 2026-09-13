# CosyVoice2-0.5B 部署笔记（含真实踩坑记录）

## 硬件要求

- **VRAM**: ~0.8GB（RTX 4070 8GB 完全够用，不 OOM）
- 对比：IndexTTS-2 需要 ~7GB + ~2GB 推理 → 8GB 卡 OOM

## 依赖地狱：为什么难装

CosyVoice2 的依赖链有三大死结：

### 问题 1: Python 版本锁死

matcha-tts（第三方语音合成库）通过 Cython 编译 C 扩展，依赖 `distutils`（Python 3.12+ 移除）。必须用 **Python 3.10**。

Python 3.10 的获取方式比较麻烦：
- `uv python install 3.10` → 从 GitHub release 下载，国内网络超时（即使走代理也慢）
- `conda create -n cosyvoice python=3.10` → 可行，但 conda 环境缺少 pip/ensurepip
- **建议**：先 `conda create -n cosyvoice python=3.10`，然后补装 pip

### 问题 2: matcha-tts 的 Cython 编译

matcha-tts 包含 Cython 编写的 monotonic alignment 扩展：

```c
error: assignment to ‘void **’ from ‘int’ makes pointer from integer without a cast
```

这是 **matcha 旧版 + numpy 新版** 的 ABI 不兼容。需要：
- numpy < 2（C API 变了）
- 安装顺序：`Cython → setuptools → matcha-tts`
- 编译时需要系统侧的 `gcc`/`g++` 和 `python3-dev`

### 问题 3: onnxruntime-gpu CUDA 版本

onnxruntime-gpu 的仓库 `https://aiinfra.pkgs.visualstudio.com/...` 在国内无法访问。
CosyVoice2 用 onnx 做 flow decoder 加速，但缺少它也能以纯 PyTorch 模式运行（稍慢）。

### 问题 4: 依赖总量炸裂

官方 `requirements.txt` 有 40+ 个包，包括：
- `deepspeed==0.15.1`（几小时安装）
- `tensorrt-cu12==10.13.3.9`（~2GB）
- `lightning==2.2.4`（PyTorch Lightning，~100MB）
- `diffusers==0.29.0`（HuggingFace diffusers）

这些对于只做推理的服务端是**不必要的**，但官方代码不做区分。

## 可行的部署路径

### 路径 A: 官方 FastAPI 服务（有完整依赖的 Python 3.10 环境）

```bash
git clone https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice
git submodule update --init --depth 1 third_party/Matcha-TTS

# 用 conda 处理 Python 3.10
conda create -n cosyvoice python=3.10
conda activate cosyvoice
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -e third_party/Matcha-TTS -i https://pypi.tuna.tsinghua.edu.cn/simple

cd runtime/python/fastapi
python server.py --port 5050
```

模型首次启动自动从 ModelScope 下载（~5.3GB），仅一次。

### 路径 B: 精简版 PyTorch 服务（跳过大部头依赖）

如果只做推理，可以只装核心依赖：

```bash
pip install torch torchaudio \
  -i https://download.pytorch.org/whl/cu130 \
  --extra-index-url https://pypi.tuna.tsinghua.edu.cn/simple

pip install fastapi uvicorn numpy modelscope soundfile \
  hyperpyyaml omegaconf einops transformers \
  -i https://pypi.tuna.tsinghua.edu.cn/simple

# matcha-tts 必须从源码装（PyPI 上没有可直接 pip install 的包）
pip install -e third_party/Matcha-TTS \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 启动验证

```bash
cd CosyVoice
PYTHONPATH=.:third_party/Matcha-TTS \
LD_LIBRARY_PATH=/usr/lib/wsl/lib \
conda run -n cosyvoice python runtime/python/fastapi/server.py --port 5050
```

验证：
```bash
# 测试零样本克隆
curl -X POST http://127.0.0.1:5050/inference_instruct2 \
  -F "tts_text=你好世界" \
  -F "instruct_text=普通话" \
  -F "prompt_wav=@ref.wav" -o output.wav
```

## API 端点

| 端点 | 参数 | 用途 |
|------|------|------|
| `POST /inference_instruct2` | tts_text, instruct_text, prompt_wav | **推荐**：指令+参考音频 |
| `POST /inference_zero_shot` | tts_text, prompt_text, prompt_wav | 零样本克隆 |
| `POST /inference_cross_lingual` | tts_text, prompt_wav | 跨语言合成 |

返回：`StreamingResponse`（WAV 二进制流）

## 参考音频要求

- 格式：WAV, mono, 16-bit PCM, **16kHz**（server.py 内部用 `load_wav(prompt_wav.file, 16000)`）
- 长度：3-15 秒
- 说话人：单角色，背景干净

## AstrBot 集成

现有插件：`xiewoc/astrbot_plugin_tts_Cosyvoice2`（76 commits，含方言/情感/function call）

插件架构：分布式部署模式（`if_seperate_serve: true`），通过 HTTP 调用独立服务。

注意：插件已 fork 到 `publieople/astrbot_plugin_tts_Cosyvoice2`，精简了依赖（只保留 `aiohttp/pydantic/pydub/multiprocess`），默认开启分布式模式。

详见 `astrbot-operations` SKILL.md 的「插件页面开发」和「TTS 语音合成」章节。
