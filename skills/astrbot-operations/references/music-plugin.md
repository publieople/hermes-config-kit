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
