---
name: hermes-napcat-qq
description: Connect Hermes Agent to QQ group chats via NapCatQQ (OneBot 11). Use for QQ bot setup, NapCat troubleshooting, or group chat authorization.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [qq, napcat, onebot, messaging, gateway, chinese]
    related_skills: [hermes-external-integration]
prerequisites:
  env_vars: [NAPCAT_TOKEN, NAPCAT_ALLOW_ALL_USERS]
  commands: [hermes, git]
---

# Hermes + NapCatQQ → QQ 群聊接入

把 Hermes 接入 QQ 群聊。NapCatQQ 是基于 NTQQ 的 OneBot v11 协议实现，作为假用户收发消息，不依赖 QQ 官方 Bot API（审核难通过）。

## 架构

```
QQ 群聊 ←→ NapCatQQ (Windows, 寄生 NTQQ)
                │
    WebSocket Client (反向 WS)
    ws://127.0.0.1:8646/napcat/ws?access_token=xxx
                │
                ↓
         Hermes Gateway (WSL/Linux)
         监听 0.0.0.0:8646/napcat/ws
```

NapCat 是 WebSocket **客户端**，主动连接 Hermes。Hermes 是服务端。这适合 NapCat 在 Windows、Hermes 在 WSL/VPS 的拓扑。

## 前提条件

- NapCat 适配器已在 Hermes 代码中（PR #17917 合入 upstream 之前，需手动切换分支，见 §获取适配器）
- Windows 上 QQ 客户端已安装
- 一个 QQ 号（建议小号）用于机器人

---

## 1. 获取 NapCat 适配器

NapCat 适配器在 PR #17917（MoeOver），未合入上游 main。

### 推荐：使用自己的 Fork（已实施）

我们已将 Publieople 的 fork (`publieople/hermes-agent`) 设为 origin，其中已合并 MoeOver 的 NapCat PR。`hermes update` 从 fork 拉，NapCat 不被覆盖。

如需同步官方更新：`git fetch upstream && git merge upstream/main`

### 备选：直接切 MoeOver 分支

```bash
cd ~/.hermes/hermes-agent
git remote add moeover https://github.com/MoeOver/hermes-agent.git
git fetch moeover main
git checkout -b napcat moeover/main
```

注意：之后 `hermes update` 会回到 upstream main，需重新切换。推荐 fork 方案。

---

## 2. 配置 Hermes 端（WSL/Linux）

```bash
# 生成 Token
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 写入 ~/.hermes/.env
echo 'NAPCAT_TOKEN=<生成的token>' >> ~/.hermes/.env
echo 'NAPCAT_ALLOW_ALL_USERS=true' >> ~/.hermes/.env
```

### 必需环境变量

| 变量 | 说明 |
|------|------|
| `NAPCAT_TOKEN` | 共享密钥，Hermes 和 NapCat 必须一致 |
| `NAPCAT_ALLOW_ALL_USERS` | 设为 `true` 允许所有人使用（测试阶段推荐） |

### 可选环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| `NAPCAT_HOST` | Hermes 监听地址 | `0.0.0.0` |
| `NAPCAT_PORT` | Hermes 监听端口 | `8646` |
| `NAPCAT_PATH` | WebSocket 路径 | `/napcat/ws` |
| `NAPCAT_ALLOWED_USERS` | 白名单用户 QQ 号（逗号分隔） | 无 |
| `NAPCAT_GROUP_ALLOWED_USERS` | 群内白名单用户 | 无 |
| `NAPCAT_ALLOWED_GROUPS` | 白名单群号 | 无 |
| `NAPCAT_MODEL` | 按渠道独立模型（例：`deepseek-v4-flash`），需在 `gateway/run.py` 中实现 `{PLATFORM}_MODEL` 支持 | 无（走全局默认） |
| `NAPCAT_CONTEXT_MODE` | `true` 时非@消息作为上下文积攒，@时才注入+回复 | 无 |
| `NAPCAT_CONTEXT_MAX_LINES` | 上下文最大行数 | 50 |

### 重启 Gateway

```bash
hermes gateway restart
# 如果卡住（常见于 Telegram 连接超时阻塞）：
pkill -f 'hermes_cli.main gateway run'
sleep 3
hermes gateway start
```

### 验证

```bash
ss -tlnp | grep 8646          # 检查端口
grep -i napcat ~/.hermes/logs/gateway.log | tail -5  # 检查日志
```

成功时日志应显示：
```
[NapCat] Reverse WebSocket listening on ws://0.0.0.0:8646/napcat/ws
✓ napcat connected
```

---

## 3. 配置 NapCat 端（Windows）

### 安装

1. 去 [NapCatQQ Releases](https://github.com/NapNeko/NapCatQQ/releases) 下载 `NapCat.Shell.Windows.OneKey.zip`（一键包，自带 QQ）
2. 解压，运行 `NapCatInstaller.exe`，等待配置完成
3. 进入生成的 `NapCat.XXXX.Shell` 目录
4. 双击 `napcat.bat` 启动

### 获取 WebUI 密码

启动控制台中找这一行，记下 token 值：
```
[NapCat] [WebUi] WebUi User Panel Url: http://127.0.0.1:6099/webui?token=xxxx
```

### 登录 QQ

1. 打开 `http://127.0.0.1:6099/webui`
2. 用上一步的 token 登录，首次需修改密码
3. 「QQ 登录」→ 扫码登录机器人 QQ 号

### 添加 WebSocket 客户端

「网络配置」→「新建」→「WebSocket 客户端」：

| 字段 | 值 |
|------|-----|
| URL | `ws://127.0.0.1:8646/napcat/ws?access_token=<NAPCAT_TOKEN>` |
| Token | 与 `NAPCAT_TOKEN` 相同 |
| 消息上报格式 | `array` |

勾选「启用」，保存。

### 验证连接

NapCat 控制台显示连接成功。Hermes 日志显示：
```
[NapCat] NapCat connected (self_id=<QQ号>, remote=127.0.0.1)
```

---

## 4. 测试

在 QQ 群聊中 @机器人发消息。成功则 Hermes 回复。

---

## 调试方法论 ⚠️

**文档优先，不要盲目试错。**

被用户纠正的教训：
- ❌ 加临时 debug log → 重启 Gateway → 看日志 → 再加 log → 再重启 → 循环
- ✅ 先查文档搞清楚协议/字段规范 → 用 Context7 / web_extract / OneBot spec → 理解后再动手

调试消息问题的正确顺序：
1. 确认 OneBot v11 事件格式（[规范](https://github.com/botuniverse/onebot-11/blob/master/event/message.md)）
2. 对照适配器源码期望的字段（`_build_message_event`, `_normalize_segments`, `_strip_self_mention`）
3. 加**精准的**调试日志（如打印 `type(message)`、`len(message)`、`raw_message[:200]`）
4. 一次性收集所有需要的诊断信息，避免反复重启

> Context7 MCP 在 Gateway 里运行，但可能未注入当前会话工具列表。回退用 `web_extract` 查文档。

---

## 消息格式深度调试

### `_build_message_event` 返回 None 的诊断链

适配器处理群消息的路径（`napcat.py`）：

```
_handle_ws_payload → _build_message_event →
  1. message_id 存在？
  2. 去重检查？
  3. message_type == "group"？
  4. group_id 存在？
  5. _normalize_segments(message) → segs
  6. _strip_self_mention(segs) → (mentioned, text)
  7. mentioned == True?  text 非空？
```

### 关键陷阱：`message` 字段类型

适配器 `_normalize_segments` 对 **string 类型** `message` 的处理：
```python
# CQ 码格式 → 用正则洗掉所有 [CQ:...] 段 → 只剩纯文本
stripped = re.sub(r"\[CQ:[^\]]*\]", "", raw_message)
# "[CQ:at,qq=2628392161] 你好" → " 你好"
```
**at 段也被洗掉了！** 后续 `_strip_self_mention` 找不到 at 段 → `mentioned=False` → 消息被丢弃。

即使 NapCat WebUI 设置 `消息上报格式: array`，也可能实际发出 string 格式。需在适配器日志中确认 `type(message)`。

### 调试日志 `[:10]` 截断陷阱

```python
list(payload.keys())[:10]   # ❌ 可能隐藏 message、group_id 等关键字段
sorted(payload.keys())       # ✅ 显示全部字段
```

### Token 终端截断

终端输出会被截断为 `i18cQg...bNKg`。必须用 Python 读 `.env` 取完整 Token：
```bash
python3 -c "with open('.env') as f: [print(l.split('=',1)[1]) for l in f if 'NAPCAT_TOKEN' in l]"
```

---

## 常见问题

### 401 Unauthorized（NapCat → Hermes）

Token 不匹配。检查：
- `NAPCAT_TOKEN` 在 Hermes `.env` 和 NapCat WebUI Token 字段**完全一致**
- 重启 Gateway 使新 Token 生效
- 可将 Token 拼在 URL 中：`ws://ip:port/path?access_token=xxx`

### Unauthorized user 日志

```
WARNING gateway.run: Unauthorized user: <QQ号> on napcat
```

需在 `.env` 中设置授权：
- 测试阶段用 `NAPCAT_ALLOW_ALL_USERS=true`
- 生产环境用 `NAPCAT_ALLOWED_USERS=QQ号1,QQ号2`
- 群聊还需 `NAPCAT_GROUP_ALLOWED_USERS` 或 `NAPCAT_ALLOWED_GROUPS`

### `napcat_call` 工具不可用 / 图片无法识别

根因：`gateway/run.py` 中 `_active_runner` 模块变量从未被赋值，`tools/napcat_tool.py` 靠它找到 NapCat adapter，始终返回 None。

修复：在 `start_gateway()` 中 runner 实例化后添加：
```python
global _active_runner
_active_runner = runner
```
并在模块级声明 `_active_runner: Optional[Any] = None`。

### `NAPCAT_ALLOW_ALL_USERS=true` 不生效

根因：`gateway/authz_mixin.py` 的 `platform_allow_all_map` 和 `platform_env_map` 缺少 `Platform.NAPCAT` 条目。

修复：在两处映射中各添加：
```python
Platform.NAPCAT: "NAPCAT_ALLOW_ALL_USERS",  # platform_allow_all_map
Platform.NAPCAT: "NAPCAT_ALLOW_FROM",       # platform_env_map
```

### Gateway 重启卡住

`hermes gateway restart` 超时通常是 Telegram 连接阻塞。直接杀进程：
```bash
pkill -f 'hermes_cli.main gateway run'
sleep 3
hermes gateway start
```

### NapCat 掉线后需重新扫码

修改 NapCat 目录下的 `quickLoginExample.bat`，底部加：
```bat
./launcher-win10-user.bat 你的QQ号
```
之后用这个 bat 启动可自动恢复登录状态。

## 群名片与身份管理

Bot 在群里的显示名称通过 `set_group_card` 设置。

```bash
napcat_call action="set_group_card" params={"card":"新名字","group_id":群号,"user_id":bot的QQ号}
```

`user_id` 必填，传 `0` 会报 `retcode=1200`。

### 身份发现流程

用户问"XX是谁"时，**不要依赖记忆缓存**。实时调 `get_group_member_list` 查三个字段：

1. **card**（群名片）— 群里显示的名字
2. **nickname**（QQ 昵称）— 账号本身的昵称  
3. **title**（群头衔）— 容易被误认为人名的陷阱字段

详细见 `references/group-identity-management.md`。

## 更新后恢复（`hermes update` 覆盖适配器）

`hermes update` 从 origin 拉最新代码，会**删除未合入 upstream 的 NapCat 适配器**。
需要恢复三个文件的修改：

| 文件 | 修改 |
|------|------|
| `gateway/platforms/napcat.py` | 从 git stash 恢复（如已 stash）或从 fork 的旧 commit cherry-pick |
| `gateway/config.py` | `Platform.NAPCAT` 枚举 + 平台启用逻辑（读取 `NAPCAT_*` env） |
| `gateway/run.py` | `NapCatAdapter` 创建代码 + `_active_runner` 赋值 + NAPCAT 加入 `_UPDATE_ALLOWED_PLATFORMS` |
| `gateway/authz_mixin.py` | `Platform.NAPCAT` 加入 `platform_allow_all_map` 和 `platform_env_map` |

**推荐使用自己的 Fork**（§获取适配器），之后 `hermes update` 从 fork 拉，不再被覆盖。

- [PR #17917](https://github.com/NousResearch/hermes-agent/pull/17917) — NapCat 适配器源码
- [NapCatQQ 文档](https://napneko.github.io/)
- [OneBot v11 消息事件规范](https://github.com/botuniverse/onebot-11/blob/master/event/message.md)
- [OneBot v11 消息段规范](https://github.com/botuniverse/onebot-11/blob/master/message/segment.md)
- `references/onebot-v11-message-spec.md` — OneBot v11 字段速查 + Hermes 适配器处理逻辑对照
- `references/group-identity-management.md` — 群成员属性三层结构 + 身份发现流程 + 常见陷阱
- `references/napcat-advanced-features.md` — 按渠道模型 + 上下文模式 + mention 检测优化的完整实现
