# Decorator quickref (AstrBot v4.x)

All decorators live in `astrbot.api.event.filter`. The actual implementation is in `astrbot.core.star.register.star_handler` and `astrbot.core.star.filter.*`. The API doc is at `https://docs.astrbot.app/dev/star/plugin-new.html` plus the wiki `en-dev-star-guides-ai`.

## Imports

```python
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.event.filter import (
    command,
    llm_tool,
    command_group,
    event_message_type,
    EventMessageType,
    on_using_llm_tool,
    on_llm_tool_respond,
)
from astrbot.api import logger
```

`register` is the class-level decorator; `command` and `llm_tool` are method-level.

## `@register`

```python
@register("plugin_id", "author", "description", "version", "repo_url")
class MyPlugin(Star):
    ...
```

`plugin_id` is what shows up in the plugin list. Should match `name` in `metadata.yaml`. `version` is informational but the journal line that confirms load shows it: `Plugin <id> (v<version>) by <author>: <desc>`.

## `@command("cmd_name")`

```python
@command("helloworld")
async def cmd_helloworld(self, event: AstrMessageEvent):
    user_name = event.get_sender_name()
    yield event.plain_result(f"Hello, {user_name}!")
```

Triggers when user types `/helloworld`. Args after the command are passed positionally if your method declares them:

```python
@command("来点")
async def cmd_specific(self, event, category: str = ""):
    # /来点 二次元 -> category="二次元"
    ...
```

For multi-arg commands, the splitter is whitespace. For spaces-in-args, you'd need a different approach (parse `event.message_str` directly).

## `@llm_tool(name="tool_name")`

```python
@llm_tool(name="my_tool")
async def tool_my(self, event: AstrMessageEvent, image_url: str = ""):
    '''One-line summary.

    Args:
        image_url(string): URL of the image to process
    '''
    return "string result"  # returned to LLM, included in next prompt
```

The `Args:` block in the docstring IS the JSON schema. Format strictly: `name(type): description`. Supported types: `string`, `number`, `object`, `array`, `boolean`. If you misspell, the schema will be empty and the tool will never be called.

Returned value: `str` is added to next LLM prompt. `None` is dropped. `yield` of `MessageEventResult` is sent to user.

## `@command_group("group_name")`

For subcommands like `/git commit`. Not commonly needed; can simulate with a single @command + arg parsing.

## `@event_message_type(EventMessageType.ALL)`

Catch every message, not just commands. Useful for keyword triggers.

```python
@event_message_type(EventMessageType.ALL)
async def on_message(self, event: AstrMessageEvent):
    if "我要看图" in event.message_str:
        return event.plain_result("...")
```

## `@on_using_llm_tool` / `@on_llm_tool_respond`

Hook into other tools' execution. Rarely needed; only when you need to intercept / monitor LLM tool calls across the system.

## Response helpers (on `event`)

| Method | Returns | Use |
|---|---|---|
| `event.plain_result(text)` | `MessageEventResult` | Text reply |
| `event.image_result(url)` | `MessageEventResult` | Image from URL (downloaded to local) |
| `event.chain_result([comp, ...])` | `MessageEventResult` | Mixed components |
| `event.make_result().file_image(path)` | chain | Local file image |
| `event.send(chain)` | `None` (awaitable) | Send immediately, then yield more |
| `event.stop_event()` | `None` | Stop event propagation |

## Event properties

- `event.message_str` — plain text of incoming message
- `event.get_sender_id()` / `event.get_sender_name()` — user id/name
- `event.unified_msg_origin` — `str` property, stable per (platform, conversation). Use as key for per-conversation state / cooldown.
- `event.get_messages()` — `list[BaseMessageComponent]`; walk to find `Image` etc.

## Async signature

**All** handlers must be `async def`. `yield` for responses (handler is an `AsyncGenerator[MessageEventResult, None]`), or `return` for a single result. Use `event.send(...)` inside if you want to send something then keep going.
