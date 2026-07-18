---
name: llamacpp-local-inference
description: Build llama.cpp from source and run local LLM inference on Linux/WSL. Covers cmake build, GGUF model download (ModelScope for China), non-interactive inference.
triggers:
  - llama.cpp 搭建 / 安装 / 编译 / 推理
  - 本地运行 LLM / 本地模型推理
  - GGUF 模型下载 / 量化模型推理
---

# llama.cpp Local Inference

Build llama.cpp from source, download a GGUF model, and run CPU inference on Linux/WSL.

## Quickstart

```bash
# 1. Clone & build
git clone --depth 1 https://github.com/ggerganov/llama.cpp.git /tmp/llama.cpp
cd /tmp/llama.cpp
cmake -B build -DGGML_CUDA=OFF -DGGML_BLAS=OFF
cmake --build build -j$(nproc) --target llama-cli

# 2. Download model (ModelScope, China-friendly)
python3 -c "
import urllib.request, os
url = 'https://modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/qwen2.5-0.5b-instruct-q2_k.gguf'
urllib.request.urlretrieve(url, '/tmp/models/model.gguf')
print(f'Done: {os.path.getsize(\"/tmp/models/model.gguf\")//1024//1024}MB')
"

# 3. Run inference (single-turn, non-interactive)
/tmp/llama.cpp/build/bin/llama-cli \
  -m /tmp/models/model.gguf \
  -p "你的提示词" \
  -n 128 -t 4 --temp 0.7 \
  -st   # CRITICAL: single-turn, otherwise enters interactive mode and hangs
```

## Key Pitfalls

### `-st` (single-turn) is mandatory
Without `-st`, llama-cli enters interactive mode even with `-p` set. The process will NEVER exit on its own — subprocess.run with capture_output will hang forever. Always use `-st` for scripted/batch inference.

### Model download: prefer ModelScope over HuggingFace
From China, HF downloads frequently reset (HTTP/2 stream cancel). ModelScope CDN is stable:
- Pattern: `https://modelscope.cn/models/{org}/{repo}/resolve/master/{filename}`
- Use `urllib.request.urlretrieve` for reliable single-shot download
- Discover files: `curl -s "https://modelscope.cn/api/v1/models/{org}/{repo}/repo/files" | python3 -c "import sys,json; ..."`

### WSL + NTFS: venv on Linux filesystem
`uv add` on NTFS-mounted projects (`/mnt/e/...`) fails with "Operation not permitted" during file copy. Workaround: create venv on Linux side:
```bash
uv venv /home/po/.venvs/project-name
ln -sf /home/po/.venvs/project-name .venv
```
But note: the symlink won't work from Windows. If the user needs to run from both WSL and Windows, delete the symlink and let uv manage its own Windows venv.

### Proxy for external downloads
User has Clash at `127.0.0.1:7890`. Prefix git/curl/uv commands:
```bash
export HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890
```

## Model Size Guide

| Model | Quant | Size | RAM needed |
|-------|-------|------|------------|
| Qwen2.5-0.5B | Q2_K | ~400MB | ~1GB |
| Qwen2.5-0.5B | Q4_K_M | ~500MB | ~1.5GB |
| Qwen2.5-1.5B | Q4_K_M | ~1GB | ~2.5GB |
| Qwen2.5-3B | Q4_K_M | ~2GB | ~4GB |

For CPU inference (no GPU needed), ensure available RAM > model size + 1GB.

## Binary Dependencies

After build, the `llama-cli` binary needs these .so files in `LD_LIBRARY_PATH`:
- `libllama.so`
- `libllama-cli-impl.so`
- `libggml.so`, `libggml-base.so`, `libggml-cpu.so`

Set via env in subprocess:
```python
env={**os.environ, "LD_LIBRARY_PATH": "/path/to/build/bin"}
```
