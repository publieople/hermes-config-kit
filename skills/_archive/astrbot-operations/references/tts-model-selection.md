# TTS 模型选型速查

本地部署 TTS 时的模型选择参考（RTX 4070 8GB 环境）。

## 模型对比

| 模型 | 显存 | 日语 | 声音克隆 | 中文 | 部署难度 | 推荐场景 |
|------|------|------|---------|------|---------|---------|
| **GPT-SoVITS (Docker)** | ~4GB | ✅ | ✅ | ✅ | ⭐⭐ | 最佳本地平衡 |
| **CosyVoice2-0.5B** | 0.8GB | ✅ | ✅ | ✅ | ⭐⭐⭐⭐ | 依赖地狱，不推荐手动装 |
| **IndexTTS-2** | 7-8GB OOM | ❌ | ✅ | ✅ | ⭐⭐⭐ | 8GB 显存极限 |
| **IndexTTS-v1** | ~4GB | ❌ | ✅ | ✅ | ⭐⭐⭐ | 不需日语时可用 |
| **Fish Speech 1.5** | ~6GB | ✅ | ✅ | ✅ | ⭐ (Docker) | 效果好但显存稍高 |

## 选型原则

1. **有日语需求**：GPT-SoVITS Docker > Fish Speech > CosyVoice2
2. **无需日语**：IndexTTS-v1 轻量够用
3. **不想碰 GPU**：Edge TTS（免费无克隆）/ FishAudio API（云端克隆）
4. **依赖卡住时**：优先换模型或换部署方式，不要死磕依赖

## 部署方式选择

| 方式 | 适用场景 | 坑 |
|------|---------|-----|
| **Docker** | 有现成镜像（GPT-SoVITS / Fish Speech） | GPU passthrough 需要 runtime 配置 |
| **Conda** | 模型需要特定 Python 版本 | 镜像源在国内不一定有所有包 |
| **Pip (uv)** | 简单依赖链 | 大包超时、版本冲突、distutils 缺失 |
| **整合包** | Windows 用户 | 不适合 WSL/服务器 |

## 下载加速

- PyPI 镜像：`-i https://pypi.tuna.tsinghua.edu.cn/simple`
- PyTorch 专用：`--extra-index-url https://download.pytorch.org/whl/cu128`
- 模型源（中国）：`--source ModelScope` / `HF_ENDPOINT=https://hf-mirror.com`
- 代理：`https_proxy=http://127.0.0.1:7890`
- uv 超时：`UV_HTTP_TIMEOUT=300`
