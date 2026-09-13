# AstrBot v4 session string format

The format that `Context.send_message(session, ...)` and the `unified_msg_origin`
canonical form expect. Getting this wrong is the #1 cause of "plugin notification
didn't reach the group" bugs.

## Canonical format

```
{platform_id}:{MessageType}:{session_id}
```

Example (the user's actual setup):

```
default:GroupMessage:923740990
```

## What each part is

### `{platform_id}` — the platform instance ID, NOT the adapter class name

Set by the user in `~/astrbot/data/cmd_config.json` under
`platforms[].id`. It can be **anything** the user picks. In the user's
setup it's `default`:

```json
{
  "platforms": [
    {
      "type": "aiocqhttp",
      "id": "default",
      "enable": true,
      "ws_reverse_host": "127.0.0.1",
      "ws_reverse_port": 6199
    }
  ]
}
```

AstrBot creates a `PlatformMetadata(id=<this id>, name="aiocqhttp", ...)`
when the adapter starts. `context.send_message` matches on `meta().id`,
NOT on `meta().name` or the adapter class.

**Common mistake**: hardcoding `aiocqhttp` as the platform_id. This
works in dev only if the user's `id` field happens to equal
`"aiocqhttp"`. Otherwise `context.send_message` returns False and logs
`cannot find platform for session aiocqhttp:..., message not sent`.

### `{MessageType}` — CamelCase enum value

From `astrbot/core/platform/message_type.py`:

```python
class MessageType(Enum):
    GROUP_MESSAGE = "GroupMessage"
    FRIEND_MESSAGE = "FriendMessage"
    OTHER_MESSAGE = "OtherMessage"
```

**Common mistake**: using the aiocqhttp event payload's lowercase `group`.
The event payload field is `event.message_type == "group"`, but
`MessageSesion.from_str()` does `MessageType(message_type)` — passing
`"group"` raises `ValueError: 'group' is not a valid MessageType`. This
gets wrapped as `不合法的 session 字符串: 'group' is not a valid MessageType`
at the plugin layer.

### `{session_id}` — the QQ group/user ID as string

For groups: the group ID (e.g. `923740990`).
For private: the user ID.

## Correct fix in plugin code

Don't hardcode `aiocqhttp` or guess at `MessageType`. Look them up from
the live `Context`:

```python
def _resolve_session(self, group_id: str) -> str:
    if group_id.count(":") >= 2:
        # Already a full session string
        return group_id
    if self.context is None:
        # Fallback for code paths that run before Context is wired
        return f"aiocqhttp:GroupMessage:{group_id}"
    for platform in self.context.platform_manager.platform_insts:
        meta = platform.meta()
        if meta.name == "aiocqhttp":
            return f"{meta.id}:GroupMessage:{group_id}"
    return f"aiocqhttp:GroupMessage:{group_id}"  # last-resort fallback
```

The fallback path is OK because the typical user setup uses `id: default`
and the lookup hits. If a user customizes their `id` to something exotic
and Context isn't wired, the fallback degrades to the (likely wrong)
hardcoded path — but that's a rare case and the error is loud.

## How to verify your session string is correct

Ask the bot to echo `event.unified_msg_origin` in any handler — that IS
the canonical string for the current event's session:

```python
@filter.command("whatsession")
async def whatsession(self, event: AstrMessageEvent):
    yield event.plain_result(f"umo: {event.unified_msg_origin}")
```

Send `/whatsession` from the group you want to test — it'll print
something like `default:GroupMessage:923740990`. Use exactly that format
when constructing your own session strings.

## Diagnostic recipe

When `context.send_message(session, chain)` silently fails or raises:

1. `journalctl -u astrbot --since '5 minutes ago' --no-pager | grep -iE 'session|platform|sender|message not sent'`
2. Check the **exact** `event.unified_msg_origin` from `/whatsession` for the
   target group — your constructed string must match field-by-field
3. Confirm `cmd_config.json` `platforms[].id` for the platform you're
   targeting — first segment of your session must equal this
4. Confirm MessageType is CamelCase — Python enum names match `GroupMessage`/`FriendMessage`/`OtherMessage`, not `group`/`friend`