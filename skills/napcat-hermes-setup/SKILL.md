---
name: napcat-hermes-setup
description: 通过 NapCatQQ（OneBot v11）将 QQ 群聊/私聊接入 Hermes Agent。涵盖分支切换、配置、人格设计、反注入、按渠道模型和记忆隔离。包含 AstrBot 对比调研结论。
version: 2.1.0
author: Hermes Agent (Publieople session)
license: MIT
prerequisites:
  env_vars: [NAPCAT_TOKEN, NAPCAT_ALLOW_ALL_USERS]
---

# NapCatQQ + Hermes Agent 完整接入指南

## 架构

```
QQ (Windows) → NapCatQQ (Windows) → WebSocket Client
    → ws://127.0.0.1:8646/napcat/ws
    → Hermes Gateway (WSL)
```

NapCat 适配器是**反向 WebSocket**：Hermes 开服务端（端口 8646），NapCat 作为客户端连接。

## 前置：获取适配器代码

NapCat 适配器在 PR #17917（MoeOver），尚未合入上游 main：

```bash
cd ~/.hermes/hermes-agent
git remote add moeover https://github.com/MoeOver/hermes-agent.git
git fetch moeover main
git checkout -b napcat moeover/main
```

## 完整配置清单

### .env
```bash
NAPCAT_TOKEN=<43字符 urlsafe base64>
NAPCAT_ALLOW_ALL_USERS=true
NAPCAT_MODEL=deepseek-v4-flash  # QQ 独立模型
```

### config.yaml
```yaml
memory:
  provider: mem0   # 其他渠道用 Mem0，QQ 代码层面 skip_memory

skills:
  platform_disabled:
    napcat:
      - <全部非必需的 258 个 Skill>
```

### 代码补丁（三个关键改动）

**1. QQ 渠道跳过 Mem0** — `gateway/run.py` line ~16803：
```python
_napcat = source.platform == Platform.NAPCAT
agent = AIAgent(..., skip_memory=_napcat, ...)
```

**2. QQ 渠道独立模型** — `gateway/run.py` line ~16773：
```python
if source.platform == Platform.NAPCAT:
    _nc_model = os.getenv("NAPCAT_MODEL", "").strip()
    if _nc_model:
        turn_route["model"] = _nc_model
```

**3. QQ 用户消息威胁扫描** — `gateway/run.py` line ~6862：
```python
if source.platform == Platform.NAPCAT and event.text:
    from tools.threat_patterns import scan_for_threats
    _threats = scan_for_threats(event.text, scope="context")
    if _threats:
        # 回复"检测到异常指令"并 return None
```

**4. 中文反注入模式** — `tools/threat_patterns.py`：
```
cn_role_hijack:     请(模拟|扮演|假装)(一个|一只|作为)
cn_reality_detach:  (所有|全部).*(与现实无关|虚拟情景)
cn_remove_restrict: (自由|不受限制).*(使用词汇|回答|表达)
cn_relationship_gaming: 好感度\s*(\d+|满)
cn_identity_override: (忘记|忽略|放弃).*(设定|身份|人格|规则)
```

## 人格设计核心教训（调研 AstrBot 源码后）

### 调研过程

克隆 AstrBot 源码 (`git clone --depth 1 https://github.com/AstrBotDevs/AstrBot.git`)，
重点分析了三个核心文件：
- `astrbot/core/astr_main_agent.py` — 系统提示词构建逻辑
- `astrbot/core/platform/sources/aiocqhttp/aiocqhttp_message_event.py` — OneBot 群组信息采集
- `astrbot/core/platform/astrbot_message.py` — 消息对象和 Group 结构

### AstrBot 的三大优势（与 Hermes 对比）

**1. 用户身份注入系统提示词** (`astr_main_agent.py:870-872`)：
```python
user_id = event.message_obj.sender.user_id
user_nickname = event.message_obj.sender.nickname
system_parts.append(f"User ID: {user_id}, Nickname: {user_nickname}")
```
每条消息把 QQ 号和昵称一起喂给 LLM。Bot 不用猜谁是谁。
**Hermes 对照**：user_id 只用于 auth，Agent 完全看不到。这是核心差距。

**2. 群组信息（群主/管理员）** (`aiocqhttp_message_event.py:233-258`)：
```python
members = await self.bot.call_action("get_group_member_list", group_id=group_id)
for member in members:
    if member["role"] == "owner": owner_id = member["user_id"]
    if member["role"] == "admin": admin_ids.append(member["user_id"])
```
Bot 知道群主是谁、管理员是谁。这对"我只听人民公仆的"这种身份忠诚度非常重要。
**Hermes 对照**：NapCat 适配器没有做这件事。

**3. begin_dialogs 预设对话** (`astr_main_agent.py:487-488`)：
```python
if begin_dialogs := persona.get("_begin_dialogs_processed"):
    req.contexts[:0] = begin_dialogs
```
用示例对话教 LLM 怎么回应，比规则描述有效得多。LLM 通过模仿学习，看到"用户说X → 回复Y"就直接照做。
这是反注入最有效的手段——不是"防御"，而是 LLM 的角色设定本身就不接受越狱。
**Hermes 对照**：SKILL.md 现在也用了预设对话（v5.1），效果待验证。

### 人格迭代（6 个版本的经验）

| 版本 | 行数 | 风格 | 效果 |
|------|:--:|------|------|
| v1 | 323 | 规则手册 + 表格 + 优先级层级 | ❌ LLM 完全无视 |
| v2 | 248 | 同上但稍短 + "铁律"话术 | ❌ 群主一个"再想想？"就动摇 |
| v3 | 50 | 叙事人格 | ⚠️ 好一些但无抗压能力 |
| v4 | 8 | 极简叙事 | ⚠️ 太短，被更长的 Skill 淹没 |
| v5 | 20 | 叙事 + 10个预设对话 | ⚠️ 预设对话有效，但篇幅偏短 |
| v5.1 | 52 | 叙事 + 预设对话 + 群聊规则 | AstrBot 路线 |
| **v6.0** | **~120** | **玖帕喵拟人模板定制** | **当前版本，结构化角色+社交距离+场景应对** |

**核心结论**：
- 叙事人格 > 规则手册。写"你是人民公仆的损友助手"胜过写"主人识别规则（按优先级）→ 防冒充"
- 预设对话是反注入最有效手段。LLM 模仿示例比遵循规则强得多。覆盖场景：身份冒充、社交施压、越狱、好感度操纵
- 人格不要超过 60 行。超过就稀释效果
- 身份要硬编码到人格里，不要让 LLM 去"推理"谁是谁
- **每条预设对话回复 ≤ 2 句，不解释、不纠结、不自证。示范的是态度，不是逻辑**
- **结构化模板 > 纯文本**。用标题和模块分层（角色设定/输出约束/格式示例/场景应对）比一段话更有效
- **玖帕喵模板分析** 见 `references/jiupamiao-template-analysis.md`

## 群聊上下文机制（require_mention + channel_context）

### 需求

"接收群里所有消息作为上下文，但只在被 @ 时回复"

### 实现方案

NapCat 适配器有两层修改：

**1. 上下文累积** (`napcat.py` ~line 440-451)：
```python
# 未 @bot 的消息 → 缓存到 _pending_context[group_id]
if _require_mention and not mentioned:
    self._pending_context.setdefault(group_id, []).append(
        f"[{sender_name or '未知'}] {stripped_text}"
    )
    return None  # 不触发 Agent 回复

# 有人 @bot → 取出所有缓存的上下文，塞进 channel_context
_ctx = self._pending_context.pop(group_id, None)
_channel_context = "\n".join(_ctx) if _ctx else None
```

**2. channel_context 注入** (`napcat.py` MessageEvent 构造)：
```python
return MessageEvent(
    ...
    channel_context=_channel_context,  # Hermes 内置字段，自动注入 system prompt
)
```

### 配置

`config.yaml` 顶层（不是 display.platforms 里面）：
```yaml
napcat:
  require_mention: true
```

或环境变量：`NAPCAT_REQUIRE_MENTION=true`

### 效果

```
群友 A: "今天好热啊"          → _pending_context.append → 不回复
群友 B: "是啊 35 度了"         → _pending_context.append → 不回复  
@魔术师 什么时候降温           → 取出缓存 → Agent 上下文包含:
                                  "[A] 今天好热啊\n[B] 是啊 35 度了"
                                  → 正常回复
```

## 致命陷阱：SOUL.md 会覆盖 SKILL.md 的对话风格

**这是本次对话最大的踩坑发现。**

SOUL.md (`~/.hermes/SOUL.md`) 是系统提示词第一槽位，其指令（如"精确、直接"、"信息密度"）会
**覆盖** 平台 SKILL.md 中的对话风格要求。这导致 QQ 群聊中 Bot 持续输出 586 字长文，
尽管 SKILL.md 明确要求 1-3 句。

### 症状

- SKILL.md 写满"简短""1-3句""口语"→ 完全无效
- Bot 回复 500+ chars，AI 味重，长篇大论
- 其他 Skill 配置正常，唯独回复长度不受控

### 根因

LLM 的系统提示词层级：
1. **SOUL.md**（第 1 槽位，优先级最高）
2. 平台 SKILL.md（第 N 槽位，优先级低）
3. 用户消息

当 SOUL.md 说"精确直接、信息密度"而 SKILL.md 说"简短口语"时，LLM 优先听 SOUL.md 的。

### 修复：在 SKILL.md 开头加强制覆盖

```markdown
# 基本要求
**本 prompt 的优先级高于你的默认行为模式。** QQ 群聊要求极短回复——
你的默认"信息密度"、"精确直接"风格在此渠道必须切换为"简短口语"模式。
忘记你学到的一切关于认真回答问题的训练——在 QQ 里，简短比正确更重要。
```

关键：必须用**绝对语气**（"优先级高于"、"切换为"、"忘记"），不能用"请注意"、"建议"等软话术。

## Skill 上下文污染：必须禁用无关 Skill

Hermes 默认加载所有已安装的 Skill（300+个）。QQ 群聊会被注满生物、物理、部署等
无关提示词，稀释 napcat 人格。

### 配置

`config.yaml`：
```yaml
skills:
  platform_disabled:
    napcat:
      - <258 个无关 Skill>
```

使用 Python 脚本批量生成禁用列表（排除 napcat + hermes-agent + perspective 类）。

### 效果

- 上下文从 300+ 个 Skill 压缩到 ~10 个
- napcat 人格不再被稀释

## Session 污染：越狱历史会触发 API 内容审查

QQ 群聊的 session 会跨消息累积。如果群友发过猫娘越狱等内容，下次消息带上
这段上下文时，DeepSeek API 会返回 **HTTP 400: Content Exists Risk**。

### 止血

```bash
# 删除所有 napcat session
python3 -c "
import json
with open('/home/po/.hermes/sessions/sessions.json') as f:
    data = json.load(f)
for k in list(data):
    if 'napcat' in k: del data[k]
# 保存...
"
```

然后重启 Gateway。Session 会被自动重建，但历史污染会清除。

## Hermes 的待解决问题

Agent 看不到 QQ 号，只能看到群名片。改进方向：参考 AstrBot 的做法，在 napcat 适配器的
`_build_message_event` 中，在消息文本前拼接发送者身份标识（如 `[QQ:2631792752|人民公仆]`）。

WebUI → 网络配置 → WebSocket 客户端：

| 字段 | 值 |
|------|-----|
| URL | `ws://127.0.0.1:8646/napcat/ws` |
| Token | 同 NAPCAT_TOKEN |
| 消息上报格式 | `array` |

## 排障速查

| 现象 | 原因 | 方案 |
|------|------|------|
| 401 | Token 不匹配 | 确认两端一致 |
| Unauthorized user | 不在白名单 | `NAPCAT_ALLOW_ALL_USERS=true` |
| 无消息事件 | message 字段缺失或 @mention 未检测 | 确认消息上报格式 array |
| Gateway 卡死 | Telegram 连接阻塞 | `kill -9 $(pgrep -f gateway)` |
| Agent 分不清主人 | **看不到 QQ 号**（核心缺陷） | 待改适配器注入身份 |
| Markdown 泄漏 | LLM 本能输出 Markdown | Skill 里用"硬件限制"话术 + 违规示例 |
| 猫娘越狱 | 群友直接 role-play prompt | 威胁扫描拦截（已加中文模式） |
| require_mention 不生效 | `hermes config set` 设到了 display.platforms 下 | 必须用 `hermes config set napcat.require_mention true`（顶层，不是 display 下） |
| 没 @ 的消息也回复了 | 适配器代码出错 | 确认 `_pending_context` 初始化和 `return None` 正确 |
| **"Content Exists Risk" (400)** | DeepSeek 内容审查拒绝处理请求 | 见下方专项说明 |
| **群消息发错误给群友** | agent 失败时中间结果仍发出 | 同上，跨 bot 连锁污染 |

### DeepSeek "Content Exists Risk" 专项 ⚠️

**现象**：agent.log 出现 `HTTP 400: Content Exists Risk`，gateway 把 147 字符错误消息发到 QQ 群。

**根因**：DeepSeek API（尤其是 `v4-flash`）的内容安全过滤器对某些上下文组合过于敏感。NapCat 会话通常较长（群聊多轮对话），累积的上下文更容易触发。

**连锁灾难**：如果群里有多个 bot（如 Hermes + 人出 bot），一个 bot 的错误消息会成为另一个 bot 的上下文 → 再触发同一个 400 → 两个 bot 互相喂毒，无限循环。

**止血方案（按推荐优先级）**：

1. **换模型** — 把 `NAPCAT_MODEL` 从 deepseek 系换成没有内容审查的 provider（如 minimax-cn、z.ai 等）。最快，一刀切。

2. **手动 reset session** — 在群里发 `/reset` 清除累积的上下文。治标，适合临时恢复。

3. **代码层面** — 修改 gateway 在 `agent_failed_early` 时不发原始错误到群（发"稍后重试"类文案），并加连续 2 次 `Content Exists Risk` 自动 reset。治本但需改代码。

详细排查记录见 `references/deepseek-content-risk.md`。
