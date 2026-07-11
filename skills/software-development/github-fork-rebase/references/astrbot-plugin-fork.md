# AstrBot Plugin Fork — concrete workflow

Companion to the **First-time fork + local personalise** section in
SKILL.md. Captures the AstrBot-specific details that bit during the
astrbot_plugin_Pic fork (ImNotBird → publieople).

## Plugin contract (must be present)

A working AstrBot plugin needs:

```
<plugin-dir>/
├── main.py         # @register + class Star, decorators, handlers
├── metadata.yaml   # name, display_name, desc, version, author, repo
├── _conf_schema.json  # optional; user-tunable config (see below)
├── requirements.txt   # optional; pip-installable deps
└── logo.png        # optional; 256x256
```

`name` in `metadata.yaml` MUST be `astrbot_plugin_<x>` for the
`@register` decorator to identify it. Plugins are loaded from
`~/astrbot/data/plugins/<name>/` on AstrBot boot or WebUI reload.

## Decorator cheat sheet (verified against AstrBot 4.x)

```python
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.event.filter import (
    event_message_type, EventMessageType,   # message-type hook
    llm_tool,                              # LLM function-call tool
    command,                               # /command name
)
from astrbot.api.message_components import *
from astrbot.api import logger

@register("plugin_name", "author", "desc", "v1.0.0", "https://repo.url")
class MyPlugin(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config or {}
        # ... read config.get("<field>", default)

    @command("看图")                  # /看图 → handler
    async def cmd(self, event: AstrMessageEvent):
        yield event.plain_result("hi")

    @llm_tool(name="send_random_pic") # LLM function-call tool
    async def llm_tool_x(self, event: AstrMessageEvent):
        '''docstring's Args: xxx(type): desc drives the tool schema'''
        yield event.image_result("https://...")
        return "已发送"

    @event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        # keyword trigger — runs on every message, check yourself
        ...
```

Critical: `llm_tool`'s function docstring is parsed by AstrBot to
generate the function-calling schema. The first line is the description;
`Args:` lines become parameter schemas. Format:

```
"""给当前对话的用户发送一张随机图片。

Args:
    category(string): 可选分类 key,留空则随机
"""
```

## _conf_schema.json gotchas

WebUI-rendered config is fully data-driven from `_conf_schema.json`.
Verified patterns in the wild:

| type | behaviour | example |
|---|---|---|
| `string` | text input | trigger words |
| `int` | number input | retry count |
| `bool` | toggle | enable flag |
| `list` + `items.type=string` | tag list / multi-line input | QQ id list |
| `list` + `items.type=string` + `options[]` + `labels[]` | checkbox group (inferred, works in practice) | category whitelist |
| `string` + `options[]` + `labels[]` | single-select dropdown | connection mode |

`options` is an array of allowed values, `labels` is the same length with
display names. **Always provide `default`** — missing defaults cause the
WebUI to render empty and confuse the user.

The official `_special` keys (`select_provider`, `select_persona`, etc.)
let the user pick from existing platform objects. Useful for "pick an
LLM provider" / "pick a persona" — but the docs say these are "internal
implementation" and may break. Stick to plain types for plugin code.

## Loading / reloading / verifying

- **Hot reload**: WebUI → Plugins → `...` → Reload. No service restart
  needed for code changes; **schema changes do require a reload** for
  the new fields to show in the config UI.
- **Verify load**: `journalctl -u astrbot --since '1m ago' | grep -E
  'plugin_<name>|Added llm tool'`. Look for:
  - `Loading plugin <name> ...`
  - `Added llm tool: <tool_name>` (only if you have `@llm_tool`)
  - `Plugin <name> (v<x>) by <author>: <desc>` (confirms metadata parsed)
- **No journal access?** The user runs AstrBot standalone (not under
  systemd). Fall back to `tail -f ~/astrbot/data/astrbot.log` (older
  AstrBot) or the WebUI console — but for `astrbot v4.x` under
  `systemd --user`, `journalctl` is the only stream.

## Config injection at __init__

The plugin constructor receives a dict-shaped `config` argument. Schema
fields show up as keys. Pattern:

```python
def __init__(self, context, config=None):
    super().__init__(context)
    cfg = config or {}
    self.max_retries = int(cfg.get("max_retries", 2))
    self.enabled_urls = [CATEGORIES[k][1] for k in (cfg.get("enabled_categories") or list(CATEGORIES.keys())) if k in CATEGORIES]
```

The config dict is mutable; `self.config.save_config()` persists
runtime changes. **Don't call `save_config` in `__init__`** — schema
adds new defaults on every reload, calling save during init can clobber
user edits in race conditions.

## Distinction from "deploy a new plugin from scratch"

If the user wants to write a brand-new plugin (not fork one), the
`astrbot-deploy` skill is the right reference for the install path,
but **the contract/decorator details above are the same**. The fork
flow vs deploy flow differ only in:
- Fork: `gh fork` upstream first, then patch
- Deploy: `gh repo create` empty, then scaffold from the helloworld
  template at github.com/Soulter/helloworld

## Common slip-ups observed

1. **Forgetting `from astrbot.api import logger`** — `import logging;
   logger = logging.getLogger(__name__)` works in the helloworld
   template but loses the platform's structured-log integration. Use
   `from astrbot.api import logger` always.
2. **Decorator name typo** — `llm_tool` is a *re-export* of
   `register_llm_tool`. Both names work in `from astrbot.api.event.filter
   import llm_tool`. The version that *doesn't* work is `@filter.llm_tool`
   (there's no such attribute on the filter module).
3. **Push to `upstream`** — never works (no write access), but the error
   message is "Repository not found" which can be misread as "remote
   missing". Check `git remote -v` first.
4. **First `commit -m "..."` with a multi-line Chinese message** —
   breaks the bash heredoc. Write to `/tmp/commit_msg.txt` and use
   `git commit -F`.
