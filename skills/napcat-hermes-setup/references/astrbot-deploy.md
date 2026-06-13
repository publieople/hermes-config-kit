# AstrBot 部署笔记（替代 Hermes NapCat）

## 决策背景

2026-06-11，经过多轮 Hermes NapCat 排障后，用户决定切换到 AstrBot。

**Hermes NapCat 的核心问题**：
1. `hermes update` 每次清掉 NapCat 代码（未合入上游），虽然 fork 解决了覆盖问题
2. QQ reply 链自动 @bot 导致非@消息也被回复——修了 `seen_text + has_reply` 仍有漏网
3. `gateway.run._active_runner` 从未赋值，导致 `napcat_call` 完全不可用（图片识别停摆）
4. Agent 看不到 QQ 号，分不清主人（AstrBot 原生支持用户身份注入）
5. 累计修改太多（config.py、run.py、napcat.py、authz_mixin.py、toolsets.py），维护成本高

**为什么选 AstrBot**：
- 原生 QQ 支持（OneBot v11）
- 用户身份注入系统提示词（`User ID + Nickname`）
- 群组信息采集（群主/管理员列表）
- DeepSeek 原生支持
- 1000+ 社区插件
- Web 管理面板，可视化配置

## 部署：`uv tool install`（实测可用）

Docker 方案因网络问题拉镜像失败，改用 uv：

```bash
# ⚠️ 包名大写：AstrBot
uv tool install AstrBot --python 3.12
# 安装到 ~/.local/bin/astrbot

# 初始化（交互式，需要 pipe Y 两次）
cd ~/astrbot
yes Y | astrbot init
# → 下载 dashboard（~10MB），创建数据目录

# 启动（前台，用于验证）
astrbot run
# → WebUI 在 http://localhost:6185
# → 初始用户名 astrbot，密码随机生成（看日志）

# 后台运行（bash nohup/disown 在 Hermes 终端不可靠，用 Python subprocess）
python3 -c "
import subprocess, os
subprocess.Popen(
    ['/home/po/.local/bin/astrbot', 'run'],
    cwd='/home/po/astrbot',
    stdout=open('/home/po/astrbot/data/astrbot.log', 'a'),
    stderr=subprocess.STDOUT,
    env={**os.environ, 'HOME': '/home/po'},
    start_new_session=True,
)
"
```

### 踩坑记录

1. **包名大小写**：PyPI 上 `astrbot`（小写）不存在，必须 `AstrBot`（首字母大写）
2. **非交互式 init**：`astrbot init` 需要确认两次（安装目录 + 安装 dashboard），用 `yes Y |` pipe
3. **后台运行**：Hermes 的 `terminal(background=true)` 不可靠（Bash wrapper 被拦截），`nohup`/`setsid`/`disown` 被拒绝。最终用 `execute_code` + `subprocess.Popen(start_new_session=True)` 成功
4. **Docker 拉取失败**：`soulter/astrbot:latest` 从 Docker Hub 和 DaoCloud 镜像都失败（国内网络问题）

## NapCat 重配置

NapCat WebUI（`http://127.0.0.1:6099/webui`）→ 网络配置 → WebSocket 客户端：

| 字段 | 旧值（Hermes） | 新值（AstrBot） |
|------|--------------|---------------|
| URL | `ws://127.0.0.1:8646/napcat/ws` | `ws://127.0.0.1:6186/ws` |
| Token | NAPCAT_TOKEN | 留空 |
| 消息格式 | array | array |

## AstrBot 配置

Web 管理面板 `http://127.0.0.1:6185`：

1. **消息平台** → 添加 → `aiocqhttp`
   - 启用：✅
   - 反向 WS 端口：`6186`
   - 消息格式：`array`

2. **服务提供商** → 添加 LLM
   - 类型：OpenAI / 兼容
   - Base URL：`https://api.deepseek.com/v1`
   - API Key：DEEPSEEK_API_KEY
   - 模型：`deepseek-chat` 或 `deepseek-reasoner`

3. **其他配置** → 管理员 ID：你的 QQ 号（不是机器人的）

## Hermes 侧清理

### 停用 NapCat

```bash
sed -i '/^NAPCAT/d' ~/.hermes/.env
kill $(ps aux | grep 'gateway run' | grep -v grep | awk '{print $2}')
```

### 切回官方 main（放弃 fork）

```bash
cd ~/.hermes/hermes-agent

# 确认当前 remote
git remote -v  # origin → fork, upstream → 官方

# 重置到官方 main
git fetch upstream
git reset --hard upstream/main

# origin 改回官方
git remote set-url origin https://github.com/NousResearch/hermes-agent.git

# 清理无用 remote
git remote remove upstream
git remote remove moeover  # 如果有
```

### 同步 fork 到上游

```bash
git remote add fork https://github.com/publieople/hermes-agent.git
git push fork main --force
git remote remove fork
```

## 端口总结

| 端口 | 服务 | 状态 |
|------|------|------|
| 6185 | AstrBot WebUI | ✅ 运行中 |
| 6186 | AstrBot 反向 WS | 等待 NapCat 连接 |
| 6099 | NapCat WebUI | Windows 端 |
| 8646 | Hermes NapCat | ❌ 已停用 |
| 8642 | Hermes API Server | ✅ 仅 feishu |
