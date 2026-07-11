# astrbot_plugin_music 安装注意事项

## 已知 Bug: VideoCardRenderer 导入错误

v2.1.2 存在类名不一致 bug：
- `main.py` 导入 `from .core.song_renderer import VideoCardRenderer`
- 但 `song_renderer.py` 中类名是 `CardRenderer`（无 Video 前缀）

**修复**：
```python
# main.py 第 18 行，改为别名导入
from .core.song_renderer import CardRenderer as VideoCardRenderer
```

加载失败后通过 API 重试：
```
POST /api/plugin/reload-failed  {"dir_name": "astrbot_plugin_music"}
```

## 配置要点

- 默认网易云 API: `https://163api.qijieya.cn`（公开无需自建）
- 需要配置代理: `http://127.0.0.1:7890`
- 发送模式默认: 卡片 → 语音 → 文件 → 文本（自动降级）
- 默认平台: 网易点歌
- 支持热评、歌词、歌单
- AI 点歌: LLM Tool 自动触发，群友说"想听XXX"即可

## 常见问题

### `ActionFailed retcode=1200 消息体无法解析`

插件想发音乐卡片（`message.type = "music"`），QQ/NapCat 不认这个消息类型。

**修复**：AstrBot WebUI → 点歌插件设置 → `send_modes` 去掉 `card(卡片模式)`。

最稳：只留 `["text(文本模式)"]`，以链接形式发送。需要快速时就 `["record(语音模式)", "text(文本模式)"]`。

**原因**：`send_modes` 是个优先级列表，排在前的模式先试，失败自动试下一个。`send_card` 捕获异常后还会 `event.send(event.plain_result(str(e)))` 把报错文本发出来，用户会看到 ActionFailed 错误信息，不是静默失败。所以要么去掉 card，要么确认 QQ 协议支持 music 消息类型。
