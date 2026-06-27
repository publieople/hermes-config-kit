# GPT-SoVITS Docker 部署

用于 AstrBot GSV TTS(本地) 提供商的底层 TTS 引擎。

## 快速启动

```bash
# 拉取镜像（约 8GB，含预训练模型）
docker run -d --name gpt-sovits --gpus all \
  -p 9880:9880 \
  -v /path/to/reference_audio:/workspace/GPT-SoVITS/reference_audio \
  -e is_half=true \
  --shm-size=16g \
  xxxxrt666/gpt-sovits:latest-cu128 \
  bash -c "rm -rf /workspace/GPT-SoVITS/GPT_SoVITS/pretrained_models && \
           ln -s /workspace/models/pretrained_models /workspace/GPT-SoVITS/GPT_SoVITS/pretrained_models && \
           python api_v2.py -a 0.0.0.0 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml"
```

## 部署关键坑

1. **模型软链**：镜像预装模型在 `/workspace/models/pretrained_models/`，但 config 文件指向 `GPT_SoVITS/pretrained_models/`（空目录）。必须删空目录后 `ln -s`。

2. **参考音频挂载**：用 `-v` 挂载宿主目录到容器内 `/workspace/GPT-SoVITS/reference_audio`。

3. **`.lower()` 问题**（见主 skill）：AstrBot 的 GSV 提供商会把 `ref_audio_path` 转小写。容器内建小写软链：
   ```bash
   docker exec gpt-sovits ln -s /workspace/GPT-SoVITS /workspace/gpt-sovits
   ```

4. **API 端点**：`GET /tts`，参数通过 query string 传递。

5. **GPU 要求**：`--gpus all` + `-e is_half=true`。RTX 4070 8GB 约 4GB 显存占用。

6. **参考音频要求**：3~10 秒 WAV, mono, 16kHz。超出会报错。

7. **使用 compose 的注意事项**：官方 docker-compose.yaml 定义了多个 service，`docker compose up` 会校验全部 service 的 volume 是否存在。Lite 版多了 ASR/UVR5 目录挂载，如果没有对应目录会报错。建议直接用 `docker run`。

## 测试

```bash
curl -s -G "http://127.0.0.1:9880/tts" \
  --data-urlencode "text=你好" \
  --data-urlencode "text_lang=zh" \
  --data-urlencode "ref_audio_path=/workspace/gpt-sovits/reference_audio/voice.wav" \
  --data-urlencode "prompt_lang=zh" \
  --data-urlencode "text_split_method=cut0" \
  -o /tmp/output.wav
```

## 获取参考音频文本（whisper ASR）

```bash
python3 -c "
import whisper
m = whisper.load_model('small')
r = m.transcribe('/path/to/audio.wav', language='ja')
print(r['text'].strip())
"
```

## 镜像详情

- 镜像：`xxxxrt666/gpt-sovits:latest-cu128`
- 工作目录：`/workspace/GPT-SoVITS`
- 预训练模型：`/workspace/models/pretrained_models/`
- 默认命令：设置模型软链后 `exec bash`（不自动启动 API）
- 需要覆盖 CMD 来启动 API 服务
