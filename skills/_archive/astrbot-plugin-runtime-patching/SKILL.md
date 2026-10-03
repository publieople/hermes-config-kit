---
name: astrbot-plugin-runtime-patching
description: QQ parsing bugs, fork drift. Hot-patch AstrBot plugins.
---

# AstrBot Plugin Runtime Patching

Patch a running AstrBot's plugins without rebuilding the bot. This skill
is for when an installed plugin behaves wrong despite correct config and
the user wants a quick in-place fix (not a full reinstall).

## When to use

- User says "插件 X 不工作了 / 报错了 / 一直说不可用" with logs pointing
  to `astrbot_plugin_<name>`.
- User reports a plugin shows wrong version in the marketplace but the
  upstream repo has moved on (fork drift).
- User's plugin command parses its `args_str` wrong when invoked via QQ
  reply.

## When NOT to use

- The bot itself fails to start (`astrbot` won't come up) — that's an
  AstrBot core / config problem, not a plugin problem.
- The plugin was never installed — go through AstrBot's plugin market
  first.
- The user wants to publish a fix upstream — that's
  `astrbot-plugin-development`; this skill is for local hot-fix only.

## Triage workflow

1. **Localise the failure**: `tail -F /home/po/astrbot/data/logs/astrbot.log`
   (rotated siblings `astrbot.YYYY-MM-DD_HH-MM-SS_xxxxxx.log`). Grep for
   the plugin name and for `ERROR` / `Traceback`. The log line that
   names a strategy / command / config key is the one to read.

2. **Read the plugin source**: `/home/po/astrbot/data/plugins/<name>/`.
   `main.py` is the entry. Each provider / strategy lives in its own
   file (`sauce_nao_strategy.py`, etc.). `metadata.yaml` has the version
   the bot believes is installed. `_conf_schema.json` lists config keys.

3. **Read AstrBot's message adapter** when a command parses wrong:
   `/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/platform/sources/aiocqhttp/aiocqhttp_platform_adapter.py`.
   This is where `event.message_str` is built. If your command handler
   sees "message_str contains quoted-message noise", the bug is in
   *your plugin's parser*, not in AstrBot (see references below).

4. **Patch in place**. Use `search_files` to find the right line range
   before `patch`. Don't rewrite the file from scratch — one guard
   in the shared resolver is smaller diff than guards in every caller.

5. **Reload, do not full restart**. WebUI 插件页 → 重载 is enough for
   pure-Python changes. Only `sudo systemctl restart astrbot` if the
   patch changed `metadata.yaml` (AstrBot reads it on startup) or
   dependencies (`requirements.txt`).

6. **Verify**. Re-trigger the failing command once and grep the log for
   the previous error string — if absent, patch landed.

## Pitfalls

- **Plugin version is cached in `data/plugins.json`** (and
  `data/plugins_custom_<md5>.json` for custom registries). The market
  shows the cached version until MD5 mismatches. Restart does not force
  refresh; the MD5 endpoint is `https://api.soulter.top/astrbot/plugins-md5`.
  When upstream is forked and the new owner hasn't pushed to
  `AstrBotDevs/AstrBot_Plugins_Collection`, the cache stays stale forever.
  Workaround: `rm -rf` the plugin dir and `git clone` the new repo, then
  reload.

- **`metadata.yaml` has no `astrbot_version` constraint check at
  runtime** (it's only a market-metadata hint). Patches that depend on
  new AstrBot core APIs need a version check you write yourself.

- **`pip install -r requirements.txt` after a plugin update will trigger
  pip 26.3 deprecation warnings** if the plugin imports `data.plugins.<x>`
  in an order pip doesn't expect. Safe to ignore until pip 26.3 actually
  enforces it. Do not "fix" by changing import paths — that breaks
  AstrBot's plugin loader.

- **Fork reinstalls wipe any in-place patch you made to `main.py`.**
  If you patch and the user later upgrades, re-apply or upstream the
  fix. Mark `ponytail:` comments so future-you knows what was local.

## References

- `references/onebot-reply-messagestr-pollution.md` — exact bug pattern
  for QQ reply-mode command parsing, with the `rfind` + whitelist
  filter fix. Read this when the log shows `未找到策略 '图片 MSG_ID:...`.
- `references/plugin-market-cache-fork-staleness.md` — when plugin
  market stays on old version after the upstream has moved.