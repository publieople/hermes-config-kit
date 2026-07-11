# Whisper Self-Host STT 配置与故障排查

## 概述

AstrBot 内置了 `openai_whisper_selfhost` STT（语音转文本）提供商。核心文件位于 AstrBot Python 包的 `astrbot/core/provider/sources/whisper_selfhosted_source.py`。

## 配置字段

| 字段 | 说明 | 必填 | 示例 |
|------|------|------|------|
| `type` | 固定 `openai_whisper_selfhost` | ✅ | `openai_whisper_selfhost` |
| `id` | 提供商 ID，STT 设置里引用这个 | ✅ | `whisper_selfhost` |
| `model` | Whisper 模型大小 | ✅ | `tiny`/`base`/`small`/`medium`/`large` |
| `whisper_device` | 推理设备 | ✅ | `cpu`/`cuda`/`mps` |

### 示例配置段（放在 `provider` 列表内）

```json
{
  "provider": "openai",
  "type": "openai_whisper_selfhost",
  "provider_type": "speech_to_text",
  "enable": true,
  "id": "whisper_selfhost",
  "model": "small",
  "whisper_device": "cuda"
}
```

### STT 启用设置（在 `provider_settings` 内）

```json
"provider_stt_settings": {
  "enable": true,
  "provider_id": "whisper_selfhost"
}
```

## 源码行为

```python
@register_provider_adapter(
    "openai_whisper_selfhost",
    "OpenAI Whisper 模型部署",
    provider_type=ProviderType.SPEECH_TO_TEXT,
)
class ProviderOpenAIWhisperSelfHost(STTProvider):
```

- 通过 `@register_provider_adapter` 注册，provider 的 `type` 字段必须与装饰器的第一个参数完全匹配
- 模型加载在 `initialize()` 中异步执行，调用 `whisper.load_model(model_name, device=device)`
- 首次初始化自动从 HuggingFace 下载模型权重到 `~/.cache/whisper/`

### `whisper_device` 解析逻辑

```python
# 实际源码（截取 self.device 已 strip + lower）：
def _resolve_device(self) -> str:
    if self.device == "mps":
        import torch
        if torch.backends.mps.is_available():
            return "mps"
        logger.warning("MPS 不可用，回退 CPU")
        return "cpu"
    if self.device != "cpu":
        logger.warning("Whisper 配置了未知 device=%s，回退 CPU。", self.device)
    return "cpu"
```

**⚠️ `cuda` 不被识别，静默回退 CPU：**
源码只显式处理了 `mps` 和 `cpu`。`whisper_device: "cuda"` 不匹配 `"mps"`，也不等于 `"cpu"`，
所以走 `self.device != "cpu"` 分支 → 打印警告 → `return "cpu"`。
日志表现为 `Whisper 模型加载完成。device=cpu`，无 error，但 GPU 未使用。

**当前可行的 workaround（每次升级后需重做）：**
```python
# patch: ~/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/provider/sources/whisper_selfhosted_source.py
# 在 'if self.device != "cpu":' 前插入：
if self.device == "cuda":
    import torch
    if torch.cuda.is_available():
        return "cuda"
    logger.warning("CUDA 不可用，回退 CPU。")
    return "cpu"
```
CPU 推理 small 模型约 5s/次，GPU 约 1s/次。如果不是 High-frequency STT 场景，CPU 也能用。

**`cuda:0` / `cuda:1` 等序列号：** Whisper 的 `load_model` 会直接传给 `torch.device()`，
但源码先走 `_resolve_device()` 就回退了。patch 后可考虑返回 `self.device`（而非硬编码 `"cuda"`）
以支持指定 GPU 编号。

## 常见故障

### "Provider whisper_selfhost not found" / 测试失败

**根因：** `openai-whisper` 和 `torch` 未安装在 AstrBot 的 Python 环境。provider 源码顶部 `import whisper` 失败 → provider 注册静默跳过 → WebUI 找不到。

**诊断：**
```bash
~/.local/share/uv/tools/astrbot/bin/python3 -c "import whisper; print(whisper.__version__)"
```

**修复：** 在 AstrBot 的 Python 环境安装 `openai-whisper`（自动携带 torch + CUDA 依赖）：

```bash
# ⚠️ 不要用 uv pip install --python <path> —— uv 的 --python 标志安装到 uv 的
#    内部 CPython base（~/.local/share/uv/python/cpython-3.12.*/），
#    不进入 AstrBot 工具自己的 site-packages（~/.local/share/uv/tools/astrbot/）。
#    必须用 AstrBot 工具自身的 python3 -m pip install。
unset PYTHONPATH
~/.local/share/uv/tools/astrbot/bin/python3 -m pip install openai-whisper \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**注意：** torch 约 532MB，网络慢时务必用镜像 + 大超时（至少 600s）。

**验证安装：**
```bash
~/.local/share/uv/tools/astrbot/bin/python3 -c "
import whisper; import torch
print('whisper:', whisper.__version__)
print('torch:', torch.__version__)
print('cuda:', torch.cuda.is_available())
"
```

**重启 AstrBot 使 provider 注册生效：**
```bash
sudo systemctl restart astrbot
```

**确认日志：**
```bash
sudo journalctl -u astrbot --since "30 seconds ago" --no-pager | grep -iE "whisper|加载|model"
```
正常应有：
- `下载或者加载 Whisper 模型中，这可能需要一些时间 ...`
- `Whisper 模型加载完成。device=cuda`

### `[Errno 2] No such file or directory: .../whisper/assets/mel_filters.npz`

**根因：** `openai-whisper` 虽然报告安装成功，但没装到 AstrBot 工具自身的 site-packages。
常见于 `uv pip install --python <tool-python>` —— uv 把包装到内部 CPython base
（`~/.local/share/uv/python/`），工具的 Python 运行时找不到它。

**诊断：**
```bash
~/.local/share/uv/tools/astrbot/bin/python3 -c "import whisper"
```
若报错 "No module named 'whisper'" 但之前 `pip install` 显示成功 → 包装错了地方。

**验证正确位置：**
```bash
ls ~/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/whisper/assets/
# 应有: mel_filters.npz  gpt2.tiktoken  multilingual.tiktoken
```

### model 字段的值

| 模型名 | 大小 | RAM/VRAM | 准确率 |
|--------|------|----------|--------|
| `tiny` | ~39 MB | ~1 GB | 最低 |
| `base` | ~74 MB | ~1 GB | 低 |
| `small` | ~244 MB | ~2 GB | 中等 ✅ 推荐 |
| `medium` | ~769 MB | ~5 GB | 高 |
| `large` | ~1.55 GB | ~10 GB | 最高 |

## 相关

- AstrBot 还支持 `whisper_api_source`（云端 Whisper API）和 `sensevoice_selfhosted_source`（自托管 SenseVoice）
- TTS 配置见 [tts-model-selection.md](tts-model-selection.md)
