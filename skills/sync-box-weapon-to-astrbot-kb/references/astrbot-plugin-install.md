# AstrBot 插件安装与排障

## 安装流程

1. `git clone <repo> /home/po/astrbot/data/plugins/<plugin_name>/`
2. 如果 git 超时：`export https_proxy=http://127.0.0.1:7890` 后重试
3. AstrBot 自动热检测新插件，**不需要重启**
4. 如果加载失败（日志有错误），修复后调用 API 重载：
   ```
   POST /api/plugin/reload-failed  {"dir_name": "<plugin_name>"}
   ```

## 常见加载失败

### 导入错误（ImportError / cannot import name）

症状：`cannot import name 'VideoCardRenderer' from ...`
原因：插件代码中类名/模块名与实际文件不符。

修复：直接 patch 导入语句，如：
```python
from .core.song_renderer import CardRenderer as VideoCardRenderer
```

## AstrBot 重启

**不要用 kill + nohup 方式**，Hermes 沙箱不支持。

AstrBot 是 systemd 服务：
```bash
sudo systemctl restart astrbot
sudo journalctl -u astrbot -f  # 实时日志
```

注意：systemd 重启后旧进程的 journal 日志会保留，但 `data/astrbot.log` 可能不再更新（日志切到 journal）。

## API 交互注意事项

在 Hermes 环境中，**必须用 `execute_code` + Python `urllib.request`** 操作 AstrBot API：

- ❌ `curl` 在 shell 中 token 会被 Hermes 红action为 `***`，导致语法错误或认证失败
- ✅ Python `urllib.request` 在 execute_code 沙箱中正常运行

## 音乐插件（astrbot_plugin_music）安装记录

- 仓库：`https://github.com/Zhalslar/astrbot_plugin_music`
- 作者：Zhalslar（同 qqadmin）
- 版本：v2.1.2
- 已修复：`VideoCardRenderer` → `CardRenderer` 别名导入
- 默认配置可用，只需加 proxy：`http://127.0.0.1:7890`
- 乐队：网易云 NodeJS API 默认地址 `https://163api.qijieya.cn`
