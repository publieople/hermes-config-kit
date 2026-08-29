# NapCat / QQ 群聊接入 Hermes

通过 NapCatQQ（OneBot v11 协议 + NTQQ 假用户）将 Hermes 接入 QQ 群聊，绕过 QQ 官方 Bot API 的群聊审核难题。

## 架构

```
QQ 群聊 ←→ NapCat (Windows) ←→ Hermes Gateway NapCat Adapter (WSL) ←→ Hermes Agent
              OneBot v11                Reverse WebSocket
           (websocket client)         ws://127.0.0.1:8646/napcat/ws
```

Hermes 运行 WebSocket 服务器（端口 8646），NapCat 作为客户端主动连接。共享 Token 认证。

## 前置条件

- Hermes 版本需包含 NapCat 平台适配器。截至 2026-06，NapCat 适配器在 PR [#17917](https://github.com/NousResearch/hermes-agent/pull/17917)（MoeOver 分支），尚未合入 main。
- Windows 端需安装 NapCatQQ 并有可用 QQ 号登录。

## 切换 Hermes 到包含 NapCat 适配器的分支

```bash
# 1. 停掉 Gateway
hermes gateway stop

# 2. 添加 PR 作者的 fork
cd ~/.hermes/hermes-agent
git remote add moeover https://github.com/MoeOver/hermes-agent.git
git fetch moeover main

# 3. 创建本地分支跟踪 PR 分支
git checkout -b napcat moeover/main

# 4. 重启 Gateway
hermes gateway start
```

后续如需回到官方 main：`git checkout main && hermes gateway restart`。

## Hermes 端配置

```bash
# 生成 Token
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 写入 .env
echo 'NAPCAT_TOKEN=你的Token' >> ~/.hermes/.env
echo 'NAPCAT_ENABLED=true' >> ~/.hermes/.env   # 也可不设，有 TOKEN 就自动启用

# 可选：自定义端口和路径
# NAPCAT_HOST=0.0.0.0  (默认)
# NAPCAT_PORT=8646      (默认)
# NAPCAT_PATH=/napcat/ws (默认)
```

重启 Gateway 后验证：

```bash
tail -20 ~/.hermes/logs/gateway.log | grep napcat
# 应看到: [NapCat] Reverse WebSocket listening on ws://0.0.0.0:8646/napcat/ws
```

## NapCat (Windows) 端配置

1. 从 [NapCat releases](https://github.com/NapNeko/NapCatQQ/releases) 下载安装
2. 启动后访问 WebUI（默认 `http://127.0.0.1:6099/webui`）
3. 登录 QQ 号
4. 在网络配置中添加 WebSocket 客户端：

| 字段 | 值 |
|------|-----|
| URL | `ws://127.0.0.1:8646/napcat/ws` |
| Token | 与 Hermes 端 `NAPCAT_TOKEN` 相同 |

## 适配器能力

- 群聊 @提及触发回复（可配置群白名单）
- 私聊消息
- 媒体文件发送（图片/语音/视频，通过 `MEDIA:` 标签）
- 群管理操作（通过 `napcat_call` 工具）
- 群历史消息读取

详见适配器自带的 NapCat skill（`skills/messaging/napcat/SKILL.md`）。

## 常见问题

### Gateway 启动后端口 8646 没有监听

Gateway 按顺序连接平台（Telegram → Discord → ... → NapCat）。如果前面的平台（如 Telegram）连接超时，会阻塞后续平台。检查日志确认 NapCat 是否已连接：

```bash
tail -f ~/.hermes/logs/gateway.log | grep -E 'napcat|platform'
```

看到 `Gateway running with N platform(s)` 即为全部就绪。

### NapCat 连接后立即断开

确认 Token 一致。NapCat 端 Token 需与 Hermes 端 `NAPCAT_TOKEN` 完全匹配。

### 群聊不响应

群聊中需 @机器人才能触发。可通过 `NAPCAT_ALLOWED_USERS` 配置群白名单。
