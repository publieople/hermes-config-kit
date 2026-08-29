# NapCat (OneBot v11) QQ 接入 Hermes

## 何时使用

用户想通过 QQ 群聊接入 Hermes，但 QQ 官方 Bot API 群聊审核难通过时。

## 架构

```
QQ 群消息 → NapCat (Windows, NTQQ hook) → OneBot v11 WebSocket Client
                                              ↓
                                          Hermes Gateway (WSL, ws://0.0.0.0:8646/napcat/ws)
                                              ↓
                                          AIAgent 回复 → NapCat → QQ 群
```

Hermes 端的 NapCat 适配器是 **Reverse WebSocket 模式**：Hermes 开 HTTP Server（端口 8646），NapCat 作为 WebSocket Client 主动连接。

## Hermes 端配置

### 0. 确认/安装适配器

NapCat 适配器在 PR #17917（MoeOver，20 commits），可能未合入 main。先检查：

```bash
ls ~/.hermes/hermes-agent/gateway/platforms/napcat.py
```

不存在则需要切换到该分支：

```bash
cd ~/.hermes/hermes-agent
git remote add moeover https://github.com/MoeOver/hermes-agent.git
git fetch moeover main
hermes gateway stop
git checkout -b napcat moeover/main
hermes gateway start
```

> ⚠️ `hermes update` 会回到 upstream main，需要手动切回 napcat 分支。

### 1. 设置环境变量

```bash
# 1) 生成并写入 Token（共享密钥，NapCat 端也要用）
python3 -c "import secrets; print(secrets.token_urlsafe(32))"  # 43 字符
echo 'NAPCAT_TOKEN=<完整token>' >> ~/.hermes/.env

# 2) 放开群聊授权（默认白名单模式，不设会静默丢弃群消息）
echo 'NAPCAT_ALLOW_ALL_USERS=true' >> ~/.hermes/.env

# 3) API Server 也需要配（端口 8642）
echo 'API_SERVER_ENABLED=true' >> ~/.hermes/.env
echo 'API_SERVER_KEY=<随机密钥>' >> ~/.hermes/.env
```

### 2. 启动/重启 Gateway

```bash
# ⚠️ hermes gateway restart 可能卡住（Telegram 超时 30s 阻塞）
# 推荐做法：先杀后启
kill -9 $(pgrep -f 'hermes_cli.main gateway run')
sleep 2
hermes gateway start
```

### 3. 验证

```bash
# 看日志确认适配器 Init
grep napcat ~/.hermes/logs/gateway.log | tail -10

# 应出现：
# [NapCat] Reverse WebSocket listening on ws://0.0.0.0:8646/napcat/ws
# ✓ napcat connected
# Gateway running with 3 platform(s)

# 确认端口
ss -tlnp | grep -E '8642|8646'
# 应显示 8642 (API Server) 和 8646 (NapCat WS) 都在监听
```

## NapCat 端配置（Windows）

### 安装 NapCatQQ

1. 去 [NapCatQQ Releases](https://github.com/NapNeko/NapCatQQ/releases) 下载 **NapCat.Shell.Windows.OneKey.zip**（一键包，自带 QQ，无需单独装 QQ）
2. 解压 → 运行 `NapCatInstaller.exe`，等待自动配置
3. 进入生成的 `NapCat.XXXX.Shell` 目录
4. 双击 `napcat.bat` 启动
5. 控制台日志中找到 WebUI 登录 token：
   ```
   [WebUi] WebUi User Panel Url: http://127.0.0.1:6099/webui?token=xxxx
   ```
6. 浏览器打开 WebUI，首次登录会要求改密码
7. 用你的**机器人 QQ 小号**扫码登录（不要用主号）

### 配置 WebSocket 客户端（接入 Hermes）

WebUI 中：

1. 左侧「网络配置」→ 右上角「新建」→ 选 **WebSocket 客户端**
2. 填写：
   - **名称**：`hermes`（随意）
   - **URL**：`ws://127.0.0.1:8646/napcat/ws`
   - **Token**：Hermes 端生成的 `NAPCAT_TOKEN`（43 位完整 token）
   - **消息上报格式**：`array`
3. 勾选「启用」，保存

### 验证连接

- NapCat 控制台应有「WebSocket 反向服务: 已启动」且无 401 错误
- Hermes 日志出现：
  ```
  [NapCat] NapCat connected (self_id=<你的QQ号>, remote=127.0.0.1)
  ```
- 在 QQ 群里 @机器人发消息测试

## NapCat 适配器认证方式

适配器 `_is_authorized_request` 检查三种方式（满足任一即可）：

1. `Authorization: Bearer <token>` header
2. `Authorization: <token>` header（裸 token）
3. URL 查询参数 `?access_token=<token>`

NapCat WebUI 的 Token 字段会通过方式 1 发送。如果 401，也可以把 token 拼到 URL 里：
`ws://127.0.0.1:8646/napcat/ws?access_token=<token>`

## 群聊消息处理流程

适配器收到群消息后的完整链路：

1. `_handle_ws_payload` 接收 OneBot event
2. `_build_message_event` 构建 MessageEvent：
   - `message_type == "group"` → 进入群聊逻辑
   - 调用 `_strip_self_mention` 检查是否有 `at` segment 且 `qq == self_id`
   - **未 @bot → 静默丢弃（返回 None，无日志）**
   - @bot 但无文本内容 → 也丢弃
3. `_dispatch_message_event` → `handle_message` → AIAgent

## 授权体系

群聊消息到达 AIAgent 前有两层授权：

| 层 | 检查项 | 环境变量 |
|----|--------|----------|
| 群/对话级 | 群 ID 是否在白名单 | `NAPCAT_ALLOWED_GROUPS`（逗号分隔群 ID） |
| 用户级 | 用户 QQ 号是否在白名单 | `NAPCAT_ALLOWED_USERS`（逗号分隔 QQ 号） |
| 全局绕过 | 允许所有用户 | `NAPCAT_ALLOW_ALL_USERS=true` |

**未授权消息在网关层被 WARNING 日志记录后静默丢弃。** 群聊中不会给用户任何提示。

## 故障排查

| 现象 | 可能原因 | 排查方法 |
|------|----------|----------|
| NapCat 401 Unauthorized | Token 不匹配或未传 | 确认 NapCat Token 字段 = HERMES .env 中 NAPCAT_TOKEN；也可把 token 拼到 URL 里 |
| NapCat 连上但群消息无反应 | 账号未授权 | 检查 gateway.log 是否有 `Unauthorized user` WARNING；设 `NAPCAT_ALLOW_ALL_USERS=true` |
| 完全无 NapCat 日志 | 适配器未启用 | 确认 `NAPCAT_TOKEN` 在 .env 中；确认 `gateway.log` 有 `Connecting to napcat...` |
| Gateway restart 卡住 | Telegram 连接超时阻塞 | 用 `kill -9` 配合 `hermes gateway start` 代替 `hermes gateway restart` |
| 消息收到但 Hermes 不响应 | @mention 未识别 | NapCat 适配器要求显式 `at` segment；确认消息 sent as array 格式包含 `{"type":"at","data":{"qq":"bot_qq"}}` |
| 需要调试消息流 | 无 INFO 日志 | 在 `_handle_ws_payload` 加 `logger.info`；参见下文调试技巧 |

## 调试技巧

适配器的 `_build_message_event` 返回 `None` 时无任何日志（正常设计，避免群聊噪音）。如需排查消息为何被丢弃，在 `gateway/platforms/napcat.py` 的 `_handle_ws_payload` 中加临时 INFO 日志：

```python
# 在 _handle_ws_payload 的 post_type 分支前添加：
logger.info("[%s] DEBUG inbound payload: post_type=%s keys=%s", 
            self.name, post_type, list(payload.keys())[:10])

# 在 message 分支的 _build_message_event 调用后添加：
logger.info("[%s] DEBUG _build_message_event returned: %s, msg_type=%s, group=%s",
           self.name, "None" if event is None else "event", 
           payload.get("message_type"), payload.get("group_id"))
```

修改后 `kill -9` 重启 gateway 生效。调试完记得移除。

## 关键环境变量汇总

```bash
# 必需
NAPCAT_TOKEN=<43字符base64token>

# 授权（至少设一个）
NAPCAT_ALLOW_ALL_USERS=true          # 放行所有人
# 或
NAPCAT_ALLOWED_USERS=QQ号1,QQ号2     # 用户白名单
NAPCAT_ALLOWED_GROUPS=群ID1,群ID2    # 群白名单

# 可选
NAPCAT_HOST=0.0.0.0                  # 监听地址（默认 0.0.0.0）
NAPCAT_PORT=8646                     # 监听端口（默认 8646）
NAPCAT_PATH=/napcat/ws               # WS 路径（默认 /napcat/ws）
NAPCAT_ENABLED=true                  # 强制启用（不设则靠 token 自动启用）
```
