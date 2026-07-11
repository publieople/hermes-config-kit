# Cooldown pattern for per-session rate limiting

Used when a plugin makes calls to a rate-limited third-party API (Sightengine 5-ops/image, free-tier quotas, etc.) and needs to prevent users from burning through the quota.

## Core pattern (~10 lines)

```python
import time

def __init__(self, context, config=None):
    ...
    self.cooldown = int(config.get("cooldown_seconds", 30))
    self._last_call: dict[str, float] = {}   # per-session timestamp dict

def _check_cooldown(self, origin: str) -> tuple[bool, int]:
    """Returns (allowed, remaining_seconds)."""
    now = time.time()
    last = self._last_call.get(origin, 0.0)
    if now - last < self.cooldown:
        return False, int(self.cooldown - (now - last)) + 1
    return True, 0

def _update_cooldown(self, origin: str):
    self._last_call[origin] = time.time()
```

## Integration in a command handler

```python
@command("my_cmd")
async def cmd_handler(self, event: AstrMessageEvent):
    origin = event.unified_msg_origin          # per-session key
    allowed, remain = self._check_cooldown(origin)
    if not allowed:
        yield event.plain_result(f"冷却中, 还剩 {remain} 秒")
        return
    self._update_cooldown(origin)
    # ... actual work
```

## Schema entry

```json
{
  "cooldown_seconds": {
    "type": "int",
    "description": "每个会话的冷却时间(秒)",
    "hint": "防止刷请求烧光免费配额,默认 30",
    "default": 30
  }
}
```

## Why `unified_msg_origin` instead of user_id

- `unified_msg_origin` is the per-session key — it scopes cooldown to the conversation (group DM / private chat), not the global user
- Same user in different groups gets separate cooldowns, which is usually what you want
- One-liner: `event.unified_msg_origin`  (returns str, property, no await needed)

## When to NOT add cooldown

- Plugin that generates local content (no external API cost)
- LLM tool that's called sparingly by the AI itself (natural throttling)
- Read-only commands that hit a local DB or static data

Ponytail: this is the smallest working pattern. `dict[str, float]` with no locks — AstrBot is single-threaded per event, race-free. Upgrade to `asyncio.Lock` only if you need to guard against concurrent `unified_msg_origin` writes from different coroutines.
