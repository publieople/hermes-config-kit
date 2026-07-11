# `_conf_schema.json` field type cookbook

The file at `~/astrbot/data/plugins/<name>/_conf_schema.json` drives the WebUI config form. The user edits values there; your `__init__` receives them as a dict.

## Basic types

```json
{
  "max_retries": { "type": "int", "default": 2, "description": "...", "hint": "..." },
  "ai_threshold": { "type": "float", "default": 0.5, "description": "..." },
  "enabled": { "type": "bool", "default": true, "description": "..." },
  "api_key": { "type": "string", "default": "", "description": "..." },
  "long_text": { "type": "text", "default": "", "description": "..." }
}
```

`text` is a multiline textarea, `string` is single-line. `text` is editable as a drag-resizable box.

## List of strings — manual entry (most common)

```json
{
  "trigger_words": {
    "type": "list",
    "description": "...",
    "default": [],
    "items": { "type": "string" }
  }
}
```

User types strings one per row. Like AngelHeart's `chat_ids` whitelist.

## List with options + labels (CHECKBOX / multi-select)

**This is the trick** — when you want checkboxes for known options with Chinese names:

```json
{
  "enabled_categories": {
    "type": "list",
    "description": "...",
    "default": [],
    "options": ["ycy", "moez", "ai", "..."],
    "labels": ["二次元自适应", "萌版自适应", "AI 自适应", "..."],
    "items": { "type": "string" }
  }
}
```

Rendered in WebUI as checkboxes. `options` is the stored value, `labels` is the display name shown next to each checkbox. `options` and `labels` must be the same length; order matters (paired by index).

If you skip `options`/`labels`, the user just types strings in a list. The runtime code is the same: `config.get("enabled_categories", [])` returns a list.

## Object (nested)

```json
{
  "timing": {
    "type": "object",
    "description": "...",
    "items": {
      "waiting_time": { "type": "float", "default": 7.0, "description": "..." },
      "llm_timeout": { "type": "float", "default": 180.0, "description": "..." }
    }
  }
}
```

At runtime: `config.get("timing", {})["waiting_time"]`.

## Special values (`_special`)

```json
{
  "provider_id": {
    "type": "string",
    "_special": "select_provider",
    "default": ""
  }
}
```

- `select_provider` / `select_provider_tts` / `select_provider_stt` — dropdown of registered providers
- `select_persona` — dropdown of personas
- `select_knowledgebase` — multi-select KBs, type must be `list`

These are **the only `select_*` values the docs sanction for plugins**. Other internal ones (select_providers, provider_pool, etc.) are "internal implementation, may change" — don't use them in plugins.

## Schema → runtime contract

- When you bump the schema (add/remove field, change default), AstrBot **auto-migrates** the saved `_config.json`: adds missing fields with defaults, removes obsolete ones.
- The `__init__(self, context, config)` of your plugin gets the merged config. Missing keys just return `None` from `config.get(key)`.
- **Edit both schema and code together.** Forgetting to update `config.get(...)` calls in main.py means the new field is silently ignored.

## Common gotchas

- `default: []` for `list` — required, otherwise migration thinks it's None.
- For checkbox lists, **default `[]` means "all enabled" in your code** (treat empty as no filter). If you want "all disabled by default", list all keys in `default`.
- `_conf_schema.json` must be valid JSON. BOM in front of file breaks parsing in some versions; check with `json.load(open(path, encoding="utf-8-sig"))`.
- After schema change, **plugin must reload** (WebUI "Reload" button or restart) for the new form to take effect.
