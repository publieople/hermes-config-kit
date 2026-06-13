# NapCat 高级配置：按渠道模型 + 上下文模式

本文档记录 Hermes NapCat 适配器的两个自定义增强功能。

> ⚠️ 这些功能仅在配置了自定义代码（fork 或手动 patch）后生效。
> `hermes update` 会覆盖修改，需用 fork 保护。

## 按渠道独立模型（`{PLATFORM}_MODEL`）

在 `gateway/run.py` 的 `_resolve_session_agent_runtime()` 方法中注入：

```python
model = _resolve_gateway_model(user_config)
# ── Per-platform model override via {PLATFORM}_MODEL env var ──
if source and source.platform:
    _plat_model_env = f"{source.platform.value.upper()}_MODEL"
    _plat_model = os.getenv(_plat_model_env, "").strip()
    if _plat_model:
        model = _plat_model
```

配置：
```bash
# .env
NAPCAT_MODEL=deepseek-v4-flash   # QQ 走 flash，其他渠道走全局默认
```

## 群聊上下文模式（`NAPCAT_CONTEXT_MODE`）

非@消息积攒为上下文，@bot 时注入。修改 `gateway/platforms/napcat.py`：

### `__init__` 中添加
```python
self._context_mode = os.getenv("NAPCAT_CONTEXT_MODE", "").lower() in {"true", "1", "yes", "all"}
self._pending_group_context: Dict[str, List[str]] = {}
self._max_context_lines = self._coerce_positive_int(os.getenv("NAPCAT_CONTEXT_MAX_LINES"), 50)
```

### `_build_message_event` 中修改 mention gating
```python
if not mentioned:
    if self._context_mode and text:
        self._add_group_context(group_id, sender_name, text)
    return None

# ... 在 mentioned=True 分支中：
if self._context_mode:
    context_block = self._drain_group_context(group_id)
    if context_block:
        stripped_text = context_block + "\n" + stripped_text
```

### 辅助方法
```python
def _add_group_context(self, group_id, sender_name, text):
    stripped = text.strip()
    if not stripped or re.match(r'^\[(图片|表情|视频|语音|文件)[:\]]', stripped):
        return  # skip pure-media
    if group_id not in self._pending_group_context:
        self._pending_group_context[group_id] = []
    buf = self._pending_group_context[group_id]
    name = sender_name or "群友"
    buf.append(f"[{name}] {stripped}")
    while len(buf) > self._max_context_lines:
        buf.pop(0)

def _drain_group_context(self, group_id):
    buf = self._pending_group_context.pop(group_id, None)
    if not buf:
        return ""
    return "[群聊上下文]\n" + "\n".join(buf) + "\n---"
```

### Mention 检测优化

QQ 回复消息时自动插入 @bot 段，需额外检查 `reply` 段：

```python
if seg_type == "reply":
    has_reply = True
    continue
# ...
if qq == self._self_id:
    if not seen_text and not has_reply:  # @bot 在开头且无 reply 段
        mentioned = True
```

配置：
```bash
# .env
NAPCAT_CONTEXT_MODE=true      # 启用上下文模式
NAPCAT_CONTEXT_MAX_LINES=50   # 最大上下文行数
```
