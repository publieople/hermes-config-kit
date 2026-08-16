# Python 3.14 + openai-whisper 兼容问题

## 问题

Python 3.14 移除了 `pkg_resources`（来自 setuptools），但 openai-whisper 的 setup.py 依赖它。

```bash
pip install openai-whisper
# → ModuleNotFoundError: No module named 'pkg_resources'
```

`--no-build-isolation` 有时能绕过去（用 venv 里已有的 setuptools），但如果 pip 创建隔离构建环境还是会失败。

## 解决方案：用 uv 建 Python 3.12 venv

```bash
uv venv --python 3.12 .venv-cuda
uv pip install --python .venv-cuda/bin/python \
  --index-url https://download.pytorch.org/whl/cu128 torch \
  openai-whisper
```

uv 自动下载 CPython 3.12.12，不需要系统预装 Python 3.12。

## 国内网络加速

```bash
uv pip install --python .venv-cuda/bin/python \
  -i https://pypi.tuna.tsinghua.edu.cn/simple openai-whisper
```

## 失败的尝试

- `pip install --no-build-isolation` — 部分环境能过，但网络慢时也超时
- `sudo pacman -S python-openai-whisper` — 装的 CPU 版，无 CUDA
- `pip install faster-whisper` — 同样超时（网络问题，非兼容问题）
- 从 GitHub clone 源码 + pip install — 需配合镜像源