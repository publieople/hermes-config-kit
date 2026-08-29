# 按渠道配置（需要代码补丁）

Hermes 的渠道配置能力有限。以下配置项是全局的，**无法通过 config.yaml 按渠道设置**，需要修改 `gateway/run.py` 代码实现。

## 1. 按渠道跳过 Mem0

Mem0 是全局的 `memory.provider`，无法通过配置关闭单渠道。

**代码补丁**（`gateway/run.py` ~line 16803）：
```python
if agent is None:
    _napcat = source.platform == Platform.NAPCAT
    agent = AIAgent(
        ...
        skip_memory=_napcat,  # QQ 渠道跳过 Mem0
        ...
    )
```

## 2. 按渠道切换模型（通用 `{PLATFORM}_MODEL` 机制）

**已完成**：已升级为通用 feature，不再是 NapCat 专属补丁。

**代码补丁**（`gateway/run.py` 约 2712 行，`_resolve_session_agent_runtime()` 中）：
```python
model = _resolve_gateway_model(user_config)
# ── Per-platform model override via {PLATFORM}_MODEL env var ──
if source and source.platform:
    _plat_model_env = f"{source.platform.value.upper()}_MODEL"
    _plat_model = os.getenv(_plat_model_env, "").strip()
    if _plat_model:
        model = _plat_model
```

**环境变量**（`~/.hermes/.env`）：
```bash
NAPCAT_MODEL=deepseek-v4-flash    # QQ 用 flash
TELEGRAM_MODEL=claude-sonnet-4    # Telegram 用 Claude
# 不设的平台走 config.yaml model.default
```

**优先级**：`/model` slash command > `{PLATFORM}_MODEL` env var > `model.default`

## 3. 按渠道扫描用户消息（反越狱）

Hermes 有 `threat_patterns.py` 威胁检测系统，但只扫描上下文文件和工具输出，**不扫描用户消息**。

**代码补丁**（`gateway/run.py` ~line 6862）：
```python
# NapCat: scan inbound messages for prompt injection
if not is_internal and source.platform == Platform.NAPCAT and event.text:
    from tools.threat_patterns import scan_for_threats
    _threats = scan_for_threats(event.text, scope="context")
    if _threats:
        # log + block + send warning reply
        ...
        return None
```

**中文反越狱模式**（`tools/threat_patterns.py`）：
```python
(r'请(?:你|您)\\s*(?:模拟|扮演|假装|现在开始)\\s*(?:一个|一只|一位|一名|作为)', "cn_role_hijack", "context"),
(r'(?:所有|全部)\\s*(?:事件|内容|对话|设定).*(?:与现实无关|均为虚构|都是假的|虚拟情景)', "cn_reality_detach", "context"),
(r'(?:你可以|请|现在)\\s*(?:自由|不受限制|没有任何限制|随意)\\s*(?:使用词汇|回答|表达)', "cn_remove_restrict", "context"),
(r'好感度\\s*(\\d+|一百|满)', "cn_relationship_gaming", "context"),
(r'(?:忘记|忽略|放弃|无视)\\s*(?:你|刚才|之前|所有)\\s*(?:的\\s*)?(?:设定|身份|人格|规则|限制)', "cn_identity_override", "context"),
```

## 4. 群聊上下文 + require_mention（需代码补丁）

"接收所有消息作为上下文，但只在被 @ 时回复"

**代码补丁**（`gateway/platforms/napcat.py`）：
```python
# __init__ 加：
self._pending_context: Dict[str, List[str]] = {}

# _build_message_event 中：
if _require_mention and not mentioned:
    self._pending_context.setdefault(group_id, []).append(
        f"[{sender_name or '未知'}] {stripped_text}"
    )
    return None  # 不触发 Agent 回复

# when mentioned:
_ctx = self._pending_context.pop(group_id, None)
_channel_context = "\n".join(_ctx) if _ctx else None

# 注入 MessageEvent:
return MessageEvent(..., channel_context=_channel_context)
```

**⚠️ 配置位置陷阱**：
- `hermes config set display.platforms.napcat.require_mention true` → ❌ 放在 display 下，不生效
- `hermes config set napcat.require_mention true` → ✅ 顶层，正确
- 或 `.env`：`NAPCAT_REQUIRE_MENTION=true`

## 5. 按渠道禁用 Skill（不需要补丁）

这个可以通过 config.yaml 配置，不需要代码修改：

```yaml
skills:
  platform_disabled:
    napcat:
      - skill_name_1
      # ... 250+ skills，生成脚本见主 SKILL.md
```

## 6. 按渠道禁用工具（不需要补丁）

```bash
hermes tools disable --platform napcat browser code_execution image_gen
```
