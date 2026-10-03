# OneBot v11 reply-mode `event.message_str` pollution

## Symptom

A `@filter.command("X")` handler receives `event.message_str` that includes
far more than the user's actual input. Typical shape on QQ via aiocqhttp
(NapCat / go-cqhttp):

```
图片 MSG_ID:2089498924)] /搜图 SauceNAO [MSG_ID:185497072]
```

User typed only `/搜图 SauceNAO` (a reply to an image). The adapter joined
the quoted-message summary, the user's text, and the bot's own MSG_ID into
one `text` segment of `event.message`.

Naive parsers like
```py
message_str = event.message_str.strip()
parts = message_str.split(maxsplit=1)
args_str = parts[1] if len(parts) > 1 else ""
```
then resolve `args_str` as the strategy/option list and fail with
"以下策略不可用: ..." because the strategy resolver receives the entire
garbage string.

## Where it comes from

`astrbot/core/platform/sources/aiocqhttp/aiocqhttp_platform_adapter.py`
builds `message_str` by concatenating `text` segments only. The polluted
string lives in a single `text` segment sent by the upstream protocol
implementation (NapCat or go-cqhttp version), not in AstrBot itself.

`event.get_message_outline()` (used for log display only) wraps quoted
message in `[引用消息(...: <text>)]` — that prefix is display-only and
does **not** affect `message_str`.

## Fix pattern (lazy + correct)

Two-layer defence, applied to `search_image_cmd` style handlers:

1. **Locate the command by `rfind`** instead of `split(maxsplit=1)`. The
   command token is always present and tends to be the *last* "X"
   occurrence in the polluted string (the user's `/X args` comes after
   the quoted summary). Slice from `idx + len(cmd)` onward.

2. **Whitelist-filter tokens** against the plugin's known command
   vocabulary (e.g. `STRATEGY_ALIAS_MAP`). Any token not in the
   whitelist is dropped. If no valid token remains, set
   `strategy_names = None` → fall through to "use all strategies".

```py
cmd_token = "搜图"
idx = message_str.rfind(cmd_token)
args_str = message_str[idx + len(cmd_token):].strip() if idx != -1 else ""

if args_str:
    from .core.constant import STRATEGY_ALIAS_MAP
    valid = [t for t in (s.strip() for s in args_str.split(","))
             if t and t.lower() in STRATEGY_ALIAS_MAP]
    strategy_names = valid or None
else:
    strategy_names = None
```

Why both layers:
- `rfind` alone is unsafe because the quoted summary may itself contain
  the command word ("[引用消息(...: 搜图)]"). The whitelist filter is the
  real defence; `rfind` only narrows the slice to reduce false positives.
- Whitelist alone is unsafe because the user's args (`saucenao`) may also
  appear as a substring of the noise.

## When this does NOT fire

- Plain (non-reply) messages: `message_str` is just the user's input.
  Naive `split(maxsplit=1)` works.
- Non-NapCat / non-go-cqhttp adapters (kook, telegram, lark, satori):
  each constructs `message_str` differently. Always read the adapter
  source before assuming this pattern applies.

## Verification recipe

Trigger a reply message in QQ:
```
/搜图        (replying to any image)
```
Then in `data/logs/astrbot.log` grep for `未找到策略`. If the line shows
a literal `图片 MSG_ID:` inside the strategy name, the plugin still has
naive parsing — apply the patch above.