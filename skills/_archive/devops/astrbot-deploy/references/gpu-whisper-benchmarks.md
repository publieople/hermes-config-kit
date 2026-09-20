# Whisper GPU 基准测试（WSL + RTX 4070 Laptop 8GB）

测试视频：3 分 32 秒 (212s) 英文歌，16kHz 单声道 WAV。

| 设备 | 模型 | 耗时 | 倍速 | 显存 |
|------|------|------|------|------|
| CPU | base | ~200s | 0.94x | — |
| **GPU** | **small** | **45.5s** | **0.21x** | ~2GB |
| GPU | medium | 95.3s | 0.45x | ~5GB |

**结论：WSL + 4070 8GB 选 small 模型最优。** medium 开销大反而更慢，且接近 8GB 上限。

注：首次运行模型下载不计入（tiny 73MB, base 139MB, small 244MB, medium 1.5GB）。
